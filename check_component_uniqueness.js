#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

/**
 * Updates one object with contents of the other.
 * Object expected to have nesting: { components: { schemas: { ... }, errors: { ... } } }
 * @param {*} globalComponents the object to be updated
 * @param {*} newComponents the object to be added to `globalComponents
 * @returns Number of encountered duplicates.
 */
function addComponents(globalComponents, newComponents, newComponentsOrigin) {
  let duplicates = 0;
  for (const componentType in newComponents) {
    if (!(componentType in globalComponents)) {
      globalComponents[componentType] = {};
      for (const componentName in newComponents[componentType]) {
        globalComponents[componentType][componentName] = newComponentsOrigin;
      }
      continue;
    }

    for (const componentName in newComponents[componentType]) {
      const newComponent = newComponents[componentType][componentName];
      const isReference = "$ref" in newComponent;
      if (componentName in globalComponents[componentType] && !isReference) {
        const previousLocation = globalComponents[componentType][componentName];
        duplicates++;
        console.error(
          `Duplicate entry in ${componentType}: ${componentName} defined in ${previousLocation} and ${newComponentsOrigin}`,
        );
      } else if (!isReference) {
        globalComponents[componentType][componentName] = newComponentsOrigin;
      }
    }
  }

  return duplicates;
}

function main() {
  const globalComponents = {};
  const specDir = "api";
  let duplicates = 0;

  console.error(
    "Temporarily ignoring starknet_metadata.json in uniqueness check. Perhaps remove it or use it better.",
  );
  for (const fileName of fs.readdirSync(specDir)) {
    if (fileName.endsWith(".json") && fileName !== "starknet_metadata.json") {
      const filePath = path.join(specDir, fileName);
      const rawSpec = fs.readFileSync(filePath);
      const specContent = JSON.parse(rawSpec);
      const newComponents = specContent["components"];
      duplicates += addComponents(globalComponents, newComponents, filePath);
    }
  }

  if (duplicates > 0) {
    process.exit(duplicates);
  } else {
    console.log("No duplicate component definitions!");
  }
}

main();
