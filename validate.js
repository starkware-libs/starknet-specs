#!/usr/bin/env node

const {
  parseOpenRPCDocument,
  validateOpenRPCDocument,
  dereferenceDocument,
} = require("@open-rpc/schema-utils-js");
const Dereferencer = require("@json-schema-tools/dereferencer");
const fs = require("fs-extra");

async function runValidation(filename) {
  try {
    let docToParse = await fileContentAsJSON(filename);
    let docToParseWithExternalRefs = await fetchExternalRefsFor(docToParse);
    let dereffedDoc = await derefAll(docToParseWithExternalRefs);

    let doc = await parseOpenRPCDocument(dereffedDoc, { dereference: true });

    const errors = validateOpenRPCDocument(doc);
    if (errors === true) {
      console.log("Ok!");
    } else {
      console.error(errors.name);
      console.error(errors.message);
    }
  } catch (exn) {
    console.error(exn && exn.message);
  }
}

/**
 * Given a JSON document with an OpenRPC schema, fetch all references pointing to schemas in external files,
 * and add them to the schemas in this document.
 * @param {JSON} docToParse The OpenRPC document
 * @returns The amended objects.
 */
async function fetchExternalRefsFor(docToParse) {
  let externalRefs = await externalRefsFrom(docToParse.components.schemas);
  let allExternalSchemas = await fetchExternalSchemas(externalRefs);
  Object.keys(allExternalSchemas).forEach(
    (key) => (docToParse.components.schemas[key] = allExternalSchemas[key]),
  );

  return docToParse;
}

/**
 * For a given dereferencer object, make sure its initial refs don't include refs that are already
 * in the ref cache it has. So it won't try to resolve these.
 *
 * @param {Dereferencer} dereffer The dereferncer object
 * @returns The amended dereferencer.
 */
function fixRefs(dereffer) {
  dereffer.refs = dereffer.refs.filter(
    (r) => dereffer.refCache[r] === undefined,
  );
  return dereffer;
}

/**
 * For a given OpenRPC document, resolve all references.
 * This takes care of working around a bug with recursive definitions.
 * @param {JSON} doc The OpenRPC document
 * @returns The document, with the references resolved.
 */
async function derefAll(doc) {
  let allSchemas = doc.components.schemas;
  let refCacheWithRecursiveRef = {
    "#/components/schemas/CONTRACT_EXECUTION_ERROR":
      allSchemas["CONTRACT_EXECUTION_ERROR"],
    "#/components/schemas/NESTED_CALL": allSchemas["NESTED_CALL"],
  };
  let dereferencerOptions = {
    refCache: refCacheWithRecursiveRef,
    rootSchema: doc,
  };
  //resolve all schemas, and remember them
  await Promise.all(
    Object.keys(allSchemas).map(async (k) => {
      let s = allSchemas[k];
      let dereffer = fixRefs(new Dereferencer.default(s, dereferencerOptions));
      allSchemas[k] = await dereffer.resolve();
      return allSchemas[k];
    }),
  );
  return doc;
}

/**
 * Retrieve external schema definitions, from other files.
 * @param {Map<string,string} externalRefs Mapping of schema definitions, pointing to external files.
 * @returns The actual referenced schema objects
 */
async function fetchExternalSchemas(externalRefs) {
  let externalFilenames = Object.values(externalRefs).map((ref) =>
    filenameFromExternalRef(ref.value),
  );
  let uniqueExtFilenames = [...new Set(externalFilenames)];
  let externalJSONPromises = uniqueExtFilenames
    .map((relative) => {
      return { key: relative, fullpath: fullPathForRefFile(relative) };
    })
    .map((entry) =>
      fileContentAsJSON(entry.fullpath).then((c) => {
        return { key: entry.key, content: c };
      }),
    );

  let externalJSONs = await Promise.all(externalJSONPromises);

  let ret = {};

  //collect all schema objects into `ret` and return it.
  externalJSONs
    .map((entry) => entry.content.components.schemas)
    //note: this means that if we have duplicates, the last file will win. not a problem for now.
    .forEach((schemaParent) =>
      Object.keys(schemaParent).forEach((k) => (ret[k] = schemaParent[k])),
    );

  return ret;
}

/**
 * Given a filename, read, parse and return the JSON content of the file.
 * @param {String} filename The filename to read the JSON from
 * @returns The parsed JS object.
 */
async function fileContentAsJSON(filename) {
  let json = await fs.readJson(filename);
  return json;
}

/**
 * Given the set of all schemas in an RPC spec document, retrieve those that reference external
 * files.
 * @param {Map<string,string>} allSchemas Mapping of schemas from keys to schema definitions
 * @returns The external schema references, keyed by their original keys.
 */
async function externalRefsFrom(allSchemas) {
  const isExternalRef = (ref) => ref && ref.length > 0 && ref.charAt(0) != "#";

  let externalKeys = Object.keys(allSchemas).filter(
    (k) =>
      allSchemas[k]["$ref"] !== undefined &&
      isExternalRef(allSchemas[k]["$ref"]),
  );
  return externalKeys.map((k) => {
    return { key: k, value: allSchemas[k]["$ref"] };
  });
}

/**
 * Extract the filename from an external reference
 * @param {String} ref The external reference
 * @returns The file name the reference refers to.
 */
const filenameFromExternalRef = (ref) => ref.split("#")[0];

//TODO: this assumes the script is run in a specific directory relative to the files.
/**
 * Given a relative path, retrieve the full path to the relative API.
 * Note this assumes the references in the file are relative to the current working directory.
 * @param {String} relative The relative path
 * @returns The full filesystem path
 */
const fullPathForRefFile = (relative) => `${process.cwd()}/${relative}`; //should canonize this

let args = process.argv.slice(2);

if (args.length > 0) {
  runValidation(args[0]);
} else console.error("Missing filename");
