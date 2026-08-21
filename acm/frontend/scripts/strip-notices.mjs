import fs from "node:fs";
import path from "node:path";

const dir = path.resolve("src/pages");
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".tsx"))) {
  const file = path.join(dir, f);
  let c = fs.readFileSync(file, "utf8");
  const o = c;
  c = c.replace(
    /import \{ PrototypeDataNotice \} from "\.\.\/components\/ui\/PrototypeDataNotice";\r?\n/g,
    "",
  );
  c = c.replace(/\n[ \t]*<PrototypeDataNotice[^>]*\/>\r?\n/g, "\n");
  c = c.replace(/\n[ \t]*<PrototypeDataNotice[\s\S]*?\/>\r?\n/g, "\n");
  if (c !== o) {
    fs.writeFileSync(file, c);
    console.log("updated", f);
  }
}
