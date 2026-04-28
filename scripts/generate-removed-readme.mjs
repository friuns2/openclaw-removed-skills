import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const repoRoot = new URL("..", import.meta.url).pathname;

function git(args) {
  return execFileSync("git", ["-C", repoRoot, ...args], {
    encoding: "utf8",
    maxBuffer: 256 * 1024 * 1024,
  });
}

function gitOrEmpty(args) {
  try {
    return git(args);
  } catch {
    return "";
  }
}

function escapeTable(value) {
  return String(value || "").replace(/\|/g, "\\|").replace(/\n/g, " ");
}

function stripQuotes(value) {
  return value
    .trim()
    .replace(/^['"]|['"]$/g, "")
    .trim();
}

function extractYamlDescription(skillMd) {
  const match = skillMd.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return "";

  const lines = match[1].split("\n");
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const singleLine = line.match(/^description:\s*(.*)$/);
    if (singleLine) return stripQuotes(singleLine[1]);

    if (/^description:\s*[>|]/.test(line)) {
      const block = [];
      for (let next = index + 1; next < lines.length; next += 1) {
        if (!/^\s+/.test(lines[next])) break;
        block.push(lines[next].trim());
      }
      return block.join(" ").trim();
    }
  }

  return "";
}

function extractJsonDescription(metaJson) {
  if (!metaJson.trim()) return "";
  try {
    const parsed = JSON.parse(metaJson);
    return (
      parsed.description ||
      parsed.desc ||
      parsed.summary ||
      parsed.openclaw?.description ||
      ""
    );
  } catch {
    return "";
  }
}

function extractDescription(row) {
  const skillMd = gitOrEmpty([
    "show",
    `${row.parentHash}:${row.skillDir}/SKILL.md`,
  ]);
  const fromSkill = extractYamlDescription(skillMd);
  if (fromSkill) return fromSkill;

  const metaJson = gitOrEmpty([
    "show",
    `${row.parentHash}:${row.skillDir}/_meta.json`,
  ]);
  return extractJsonDescription(metaJson);
}

const currentSkillPaths = new Set(
  git(["ls-tree", "-r", "--name-only", "HEAD"])
    .split("\n")
    .filter((path) => /^skills\/[^/]+\/[^/]+\/SKILL\.md$/.test(path)),
);

const deleteLog = git([
  "log",
  "--all",
  "--grep=^delete: skills/",
  "--regexp-ignore-case",
  "--format=%H%x09%P%x09%ad%x09%s%x1e",
  "--date=short",
]);

const rows = [];
const seen = new Set();

for (const record of deleteLog.split("\x1e")) {
  const trimmed = record.trim();
  if (!trimmed) continue;

  const [hash, parentHashes, deletedDate, subject] = trimmed.split("\t");
  const match = subject.match(/^delete:\s+(skills\/[^/]+\/[^/]+)\s*(.*)$/i);
  if (!match) continue;

  const skillDir = match[1].replace(/\/$/, "");
  const skillMd = `${skillDir}/SKILL.md`;
  if (currentSkillPaths.has(skillMd) || seen.has(skillDir)) continue;
  seen.add(skillDir);

  const [, owner, skill] = skillDir.split("/");
  const parentHash = parentHashes.split(" ")[0];

  rows.push({
    owner,
    skill,
    skillDir,
    deletedDate,
    deleteFullHash: hash,
    deleteHash: hash.slice(0, 10),
    parentHash,
  });
}

rows.sort(
  (a, b) =>
    b.deletedDate.localeCompare(a.deletedDate) ||
    a.skillDir.localeCompare(b.skillDir),
);

for (const row of rows) {
  row.description = extractDescription(row);
}

const zvecRows = rows.filter((row) => /zvec/i.test(row.skillDir));

function skillLink(row) {
  return `[${row.skillDir}](https://github.com/openclaw/skills/tree/${row.parentHash}/${row.skillDir})`;
}

function commitLink(row) {
  return `[\`${row.deleteHash}\`](https://github.com/openclaw/skills/commit/${row.deleteFullHash})`;
}

function groupByDay(items) {
  const groups = new Map();
  for (const row of items) {
    if (!groups.has(row.deletedDate)) groups.set(row.deletedDate, []);
    groups.get(row.deletedDate).push(row);
  }
  return [...groups.entries()];
}

function tableForRows(items) {
  let table = "| Owner | Skill | Description | Path | Delete commit |\n";
  table += "| --- | --- | --- | --- | --- |\n";
  for (const row of items) {
    table += `| ${escapeTable(row.owner)} | ${escapeTable(row.skill)} | ${escapeTable(row.description)} | ${skillLink(row)} | ${commitLink(row)} |\n`;
  }
  return table;
}

let output = "";
output += "# Removed OpenClaw Skills\n\n";
output += "Generated from `https://github.com/openclaw/skills` git history.\n\n";
output +=
  "This file lists root skill directories that have a `delete: skills/<owner>/<skill>` commit in history and whose root `SKILL.md` is not present in `HEAD`. It is grouped by removed date, newest first. Skill links point to the last tree before deletion.\n\n";
output += `Total removed root skills found: ${rows.length}.\n\n`;
output += "## Recovery\n\n";
output += "For any row below, recover the last version before deletion with:\n\n";
output += "```bash\n";
output += "git -C skills checkout <delete-commit>^ -- <skill-path>\n";
output += "```\n\n";
output += "For example, the zvec skill can be recovered with:\n\n";
output += "```bash\n";
output +=
  "git -C skills checkout f36973c80e^ -- skills/emre-koc/zvec-local-rag-service\n";
output += "```\n\n";
output += "## zvec\n\n";
output += "| Skill | Description | Removed | Delete commit |\n";
output += "| --- | --- | --- | --- |\n";
for (const row of zvecRows) {
  output += `| ${skillLink(row)} | ${escapeTable(row.description)} | ${row.deletedDate} | ${commitLink(row)} |\n`;
}
output += "\n";
output += "## Removed Skills\n\n";
for (const [date, dateRows] of groupByDay(rows)) {
  output += `<details>\n`;
  output += `<summary>${date} (${dateRows.length})</summary>\n\n`;
  output += tableForRows(dateRows);
  output += "\n</details>\n\n";
}

writeFileSync(new URL("../README.md", import.meta.url), output);

console.log(`Wrote README.md with ${rows.length} removed skills.`);
if (zvecRows.length) {
  console.log(
    `zvec: ${zvecRows
      .map((row) => `${row.skillDir} ${row.deletedDate} ${row.deleteHash}`)
      .join("; ")}`,
  );
}
