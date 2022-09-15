#!/usr/bin/env node

const { parseOpenRPCDocument, validateOpenRPCDocument } = require("@open-rpc/schema-utils-js");
const { fileContentAsJSON, derefAll, fetchExternalRefsFor } = require('./rpc_doc_utils')

async function runValidation(filename) {
    try {
        let docToParse = await fileContentAsJSON(filename)
        let docToParseWithExternalRefs = await fetchExternalRefsFor(docToParse);
        let dereffedDoc = await derefAll(docToParseWithExternalRefs);

        let doc = await parseOpenRPCDocument(dereffedDoc, { dereference: true });

        const errors = validateOpenRPCDocument(doc);
        if (errors === true) {
            console.log("Ok!")
        } else {
            console.error(errors.name)
            console.error(errors.message)
        }
    }
    catch (exn) {
        console.error(exn && exn.message)
    }
}


let args = process.argv.slice(2);

if (args.length > 0) {
    runValidation(args[0])
}
else
    console.error("Missing filename");

