#!/usr/bin/env node

const { parseOpenRPCDocument, validateOpenRPCDocument } = require("@open-rpc/schema-utils-js");
const Dereferencer = require("@json-schema-tools/dereferencer");
const fs = require('fs-extra');
const path = require('path');

/**
 * Prints to STDERR and exits with a non-zero exit code
 * @param {string} msg 
 */
function exitWithError(msg) {
    console.error(msg);
    process.exit(1);
}

async function runValidation(filename) {
    process.stdout.write(`Validating ${filename}: `);
    try {
        let docToParse = await fileContentAsJSON(filename);
        assertVersion(docToParse);

        let parentDir = path.dirname(filename);
        let docToParseWithExternalRefs = await fetchExternalRefsFor(docToParse, parentDir);
        let dereffedDoc = await derefAll(docToParseWithExternalRefs);

        let doc = await parseOpenRPCDocument(dereffedDoc, { dereference: true });

        const errors = validateOpenRPCDocument(doc);
        if (errors === true) {
            console.log("Ok!");
        } else {
            console.error(errors.name);
            exitWithError(errors.message);
        }
    }
    catch (exn) {
        exitWithError(exn && exn.message);
    }
}

/**
 * Given a JSON document with an OpenRPC schema, fetch all references pointing to schemas in external files,
 * and add them to the schemas in this document.
 * @param {JSON} docToParse The OpenRPC document
 * @param {string} parentDir The parent directory of docToParse
 * @returns The amended objects.
 */
async function fetchExternalRefsFor(docToParse, parentDir) {
    let externalRefs = await externalRefsFrom(docToParse.components.schemas);
    let allExternalSchemas = await fetchExternalSchemas(externalRefs, parentDir);
    Object.keys(allExternalSchemas).forEach(key => docToParse.components.schemas[key] = allExternalSchemas[key]);

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
    dereffer.refs = dereffer.refs.filter(r => dereffer.refCache[r] === undefined);
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
        "#/components/schemas/NESTED_CALL": allSchemas["NESTED_CALL"]
    }
    let dereferencerOptions = {
        refCache: refCacheWithRecursiveRef,
        rootSchema: doc
    }
    //resolve all schemas, and remember them
    await Promise.all(Object.keys(allSchemas).map(async k => {
        let s = allSchemas[k]
        let dereffer = fixRefs(new Dereferencer.default(s, dereferencerOptions));
        allSchemas[k] = await dereffer.resolve();
        return allSchemas[k];
    }))
    return doc;
}


/**
 * Retrieve external schema definitions, from other files.
 * @param {Map<string,string} externalRefs Mapping of schema definitions, pointing to external files.
 * @param {string} parentDir The parent directory of the file where the references were used
 * @returns The actual referenced schema objects
 */
async function fetchExternalSchemas(externalRefs, parentDir) {
    let externalFilenames = Object.values(externalRefs).map(ref => filenameFromExternalRef(ref.value));
    let uniqueExtFilenames = [...new Set(externalFilenames)];
    let externalJSONPromises = uniqueExtFilenames
        .map(relative => ({ key: relative, fullpath: path.join(parentDir, relative) }))
        .map(entry => fileContentAsJSON(entry.fullpath).then(c => {
            return { key: entry.key, content: c }
        }));

    let externalJSONs = await Promise.all(externalJSONPromises);

    let ret = {};

    //collect all schema objects into `ret` and return it.
    externalJSONs
        .map(entry => entry.content.components.schemas)
        //note: this means that if we have duplicates, the last file will win. not a problem for now.
        .forEach(schemaParent => Object.keys(schemaParent)
            .forEach(k => ret[k] = schemaParent[k]))

    return ret;
}

/**
 * Given a filename, read, parse and return the JSON content of the file.
 * @param {String} filename The filename to read the JSON from
 * @returns The parsed JS object.
 */
async function fileContentAsJSON(filename) {
    let json = await fs.readJson(filename)
    return json
}

/**
 * Given the set of all schemas in an RPC spec document, retrieve those that reference external
 * files.
 * @param {Map<string,string>} allSchemas Mapping of schemas from keys to schema definitions
 * @returns The external schema references, keyed by their original keys.
 */
async function externalRefsFrom(allSchemas) {

    const isExternalRef = ref => ref && ref.length > 0 && ref.charAt(0) != "#";

    let externalKeys = Object.keys(allSchemas)
        .filter(k =>
            allSchemas[k]["$ref"] !== undefined && isExternalRef(allSchemas[k]["$ref"]))
    return externalKeys.map(k => { return { key: k, value: allSchemas[k]["$ref"] }; });
}

/**
 * Extract the filename from an external reference
 * @param {String} ref The external reference
 * @returns The file name the reference refers to.
 */
const filenameFromExternalRef = ref => ref.split("#")[0];

/**
 * Exits if candidateObj version not the same as in package.json
 * @param {JSON} candidateObj
 */
function assertVersion(candidateObj) {
    const candidateVersion = candidateObj.info.version;
    const expected = require("./package.json").version;
    if (candidateVersion !== expected) {
        exitWithError(`Version mismatch; expected ${expected}, got ${candidateVersion}`);
    }
}

let args = process.argv.slice(2);

if (args.length === 1) {
    runValidation(args[0]);
} else {
    exitWithError(`Error: ${__filename} <SPEC_FILE>`);
}
