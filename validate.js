#!/usr/bin/env node

// const { types } = require("@open-rpc/meta-schema");
const { parseOpenRPCDocument, validateOpenRPCDocument } = require("@open-rpc/schema-utils-js");

async function runValidation(filename) {

    try {
        let doc = await parseOpenRPCDocument(filename);

        const errors = validateOpenRPCDocument(doc);
        if (errors === true) {
            console.log("Ok!")
        }
        else {
            console.error(errors.name)
            console.error(errors.message)
        }
    }
    catch (exn) {
        console.error(exn && exn.message)
    }
}

////

let args = process.argv.slice(2);

if (args.length > 0) {
    runValidation(args[0]);
}
else
    console.error("Missing filename");

