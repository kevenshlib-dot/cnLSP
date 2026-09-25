package cnlsp;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;
import org.folio.rspec.domain.dto.SpecificationDto;
import org.folio.rspec.domain.dto.ValidationError;
import org.folio.rspec.validation.SpecificationGuidedValidator;
import org.marc4j.marc.DataField;
import org.marc4j.marc.MarcFactory;
import org.marc4j.marc.Record;

/**
 * PoC-1 验证工装：用平台 API 导出的规格 JSON（含 CNMARC 本地字段与规则开关）
 * 驱动 FOLIO 官方验证器库，验证 CNMARC 记录。
 *
 * 用法: mvn -q compile exec:java -Dexec.args="/path/to/spec-full.json"
 */
public class ValidatePoc {

  public static void main(String[] args) throws Exception {
    String specPath = args.length > 0 ? args[0] : "/tmp/spec-full.json";
    ObjectMapper mapper = new ObjectMapper()
        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    SpecificationDto spec = mapper.readValue(Files.readString(Path.of(specPath)), SpecificationDto.class);
    System.out.printf("规格: %s | family=%s | 字段=%d | 规则=%d%n",
        spec.getTitle(), spec.getFamily(), spec.getFields().size(), spec.getRules().size());

    // 翻译提供者：直接回显 key（验证消息的可读性不影响规则判定）
    SpecificationGuidedValidator validator = new SpecificationGuidedValidator((key, a) -> key);

    MarcFactory f = MarcFactory.newInstance();

    // ---- 记录 A：合规 CNMARC 记录 ----
    Record recA = f.newRecord("00000nam a2200000 a 4500");
    recA.addVariableField(f.newControlField("001", "cnlsp000001"));
    DataField a200 = f.newDataField("200", '1', '#');
    a200.addSubfield(f.newSubfield('a', "红楼梦"));
    a200.addSubfield(f.newSubfield('f', "曹雪芹著"));
    a200.addSubfield(f.newSubfield('9', "hong lou meng"));
    recA.addVariableField(a200);
    DataField a210 = f.newDataField("210", '#', '#');
    a210.addSubfield(f.newSubfield('a', "北京"));
    a210.addSubfield(f.newSubfield('c', "人民文学出版社"));
    a210.addSubfield(f.newSubfield('d', "2008"));
    recA.addVariableField(a210);
    DataField a690 = f.newDataField("690", '#', '#');
    a690.addSubfield(f.newSubfield('a', "I242.47"));
    a690.addSubfield(f.newSubfield('v', "5"));
    recA.addVariableField(a690);
    DataField a701 = f.newDataField("701", '#', '0');
    a701.addSubfield(f.newSubfield('a', "曹雪芹"));
    a701.addSubfield(f.newSubfield('4', "著"));
    recA.addVariableField(a701);

    // ---- 记录 B：多处违规 ----
    // 1) 200 缺必备子字段 $a；2) 200 ind1=9 不在定义代码表；3) 999 未定义字段（undefinedField 已启用）
    Record recB = f.newRecord("00000nam a2200000 a 4500");
    recB.addVariableField(f.newControlField("001", "cnlsp000002"));
    DataField b200 = f.newDataField("200", '9', '#');
    b200.addSubfield(f.newSubfield('f', "佚名著"));
    recB.addVariableField(b200);
    DataField b999 = f.newDataField("999", '#', '#');
    b999.addSubfield(f.newSubfield('a', "本地遗留字段"));
    recB.addVariableField(b999);

    report(validator, spec, recA, "A（合规 CNMARC）");
    report(validator, spec, recB, "B（违规记录）");
  }

  private static void report(SpecificationGuidedValidator validator, SpecificationDto spec,
      Record rec, String name) {
    Collection<ValidationError> errors = validator.validate(rec, spec);
    System.out.printf("%n== 记录 %s ==%n", name);
    if (errors.isEmpty()) {
      System.out.println("  ✓ 验证通过，无问题");
    } else {
      for (ValidationError e : errors) {
        System.out.printf("  x [%s] 规则=%s | 位置=%s | %s%n",
            e.getSeverity(), e.getRuleCode(), e.getPath(), e.getMessage());
      }
    }
  }
}
