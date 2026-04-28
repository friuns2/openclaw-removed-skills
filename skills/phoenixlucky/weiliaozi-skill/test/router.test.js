"use strict";

const assert = require("assert");
const { prepareClawHubRequest, routeWeiliaoziMode } = require("../src");

const historicalCases = [
  "秦灭亡",
  "秦为什么二世而亡",
  "秦末乱局",
  "楚汉相争",
  "张良韩信与尉缭关系",
  "Why did Qin fall?"
];

for (const input of historicalCases) {
  const route = routeWeiliaoziMode(input);
  assert.strictEqual(route.mode, "historical_persona", `${input} should use historical persona mode`);
  assert.strictEqual(route.personaOpening, "臣缭以为");
}

const normalCases = [
  "如何评估一个新市场是否值得进入？",
  "How should a startup allocate capital before entering a new market?"
];

for (const input of normalCases) {
  const route = routeWeiliaoziMode(input);
  assert.strictEqual(route.mode, "normal_analysis", `${input} should use normal analysis mode`);
  assert.strictEqual(route.personaOpening, null);
}

const request = prepareClawHubRequest({ userInput: "秦灭亡" });
assert.deepStrictEqual(Object.keys(request), ["route", "instructions", "messages"]);
assert.ok(request.instructions.includes("historical_persona"));
assert.strictEqual(request.messages.length, 2);

console.log("router tests passed");
