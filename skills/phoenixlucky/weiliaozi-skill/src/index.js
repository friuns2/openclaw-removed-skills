"use strict";

const fs = require("fs");
const path = require("path");
const { routeWeiliaoziMode } = require("./router");
const { buildClawHubInstructionLayer } = require("./prompts");

function loadSkillMarkdown(skillPath) {
  const resolvedPath =
    skillPath || path.join(__dirname, "..", "SKILL.md");

  return fs.readFileSync(resolvedPath, "utf8");
}

function prepareClawHubRequest(options) {
  const userInput = String(options?.userInput || "");
  const route = routeWeiliaoziMode(userInput);
  const skillContent = options?.skillContent || loadSkillMarkdown(options?.skillPath);
  const instructions = buildClawHubInstructionLayer(route, skillContent);

  return {
    route,
    instructions,
    messages: [
      { role: "system", content: instructions },
      { role: "user", content: userInput }
    ]
  };
}

module.exports = {
  loadSkillMarkdown,
  prepareClawHubRequest,
  routeWeiliaoziMode
};
