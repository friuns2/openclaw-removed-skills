import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const repoRoot = new URL("..", import.meta.url).pathname;

function git(args) {
  return execFileSync("git", ["-C", repoRoot, ...args], {
    encoding: "utf8",
    maxBuffer: 256 * 1024 * 1024,
  });
}

function escapeTable(value) {
  return String(value || "").replace(/\|/g, "\\|").replace(/\n/g, " ");
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
  "--format=%H%x09%ad%x09%s%x09%b%x1e",
  "--date=short",
]);

const rows = [];
const seen = new Set();

for (const record of deleteLog.split("\x1e")) {
  const trimmed = record.trim();
  if (!trimmed) continue;

  const [hash, deletedDate, subject, ...bodyParts] = trimmed.split("\t");
  const match = subject.match(/^delete:\s+(skills\/[^/]+\/[^/]+)\s*(.*)$/i);
  if (!match) continue;

  const skillDir = match[1].replace(/\/$/, "");
  const skillMd = `${skillDir}/SKILL.md`;
  if (currentSkillPaths.has(skillMd) || seen.has(skillDir)) continue;
  seen.add(skillDir);

  const body = bodyParts.join("\t").trim();
  const explicitReason = match[2].trim();
  const reason = explicitReason || body || subject;
  const [, owner, skill] = skillDir.split("/");

  rows.push({
    owner,
    skill,
    skillDir,
    deletedDate,
    deleteHash: hash.slice(0, 10),
    reason,
  });
}

rows.sort(
  (a, b) =>
    b.deletedDate.localeCompare(a.deletedDate) ||
    a.skillDir.localeCompare(b.skillDir),
);

const zvecRows = rows.filter((row) => /zvec/i.test(row.skillDir));

let output = "";
output += "# Removed OpenClaw Skills\n\n";
output += "Generated from `https://github.com/openclaw/skills` git history.\n\n";
output +=
  "This file lists root skill directories that have a `delete: skills/<owner>/<skill>` commit in history and whose root `SKILL.md` is not present in `HEAD`. It is sorted by removed date, newest first.\n\n";
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
output += "| Skill | Removed | Delete commit | Removal reason |\n";
output += "| --- | --- | --- | --- |\n";
for (const row of zvecRows) {
  output += `| \`${row.skillDir}\` | ${row.deletedDate} | \`${row.deleteHash}\` | ${escapeTable(row.reason)} |\n`;
}
output += "\n";
output += "## Removed Skills\n\n";
output += "| Owner | Skill | Path | Removed | Delete commit | Removal reason |\n";
output += "| --- | --- | --- | --- | --- | --- |\n";
for (const row of rows) {
  output += `| ${escapeTable(row.owner)} | ${escapeTable(row.skill)} | \`${row.skillDir}\` | ${row.deletedDate} | \`${row.deleteHash}\` | ${escapeTable(row.reason)} |\n`;
}

writeFileSync(new URL("../readme-removed.md", import.meta.url), output);

console.log(`Wrote readme-removed.md with ${rows.length} removed skills.`);
if (zvecRows.length) {
  console.log(
    `zvec: ${zvecRows
      .map((row) => `${row.skillDir} ${row.deletedDate} ${row.deleteHash}`)
      .join("; ")}`,
  );
}
