#!/usr/bin/env node

const fs = require('fs-extra');
const { parseOpenRPCDocument } = require("@open-rpc/schema-utils-js");

const pointer = require('json-pointer');
const { fileContentAsJSON, derefAll, fetchExternalRefsFor } = require('./rpc_doc_utils')

function parseEmbedding(emb) {

    let a = emb.emb_ptr.split(':')
    if (a.length < 2) return undefined
    let qualifier = a[0];
    let ref = a[1];
    return { qualifier, ref, ...emb }
}

function findRPCEmbeddings(source) {

    let re = /(?<emb><!--(?<ptr>[^\-\-\>]*)\-\-\>)/g //match and capture anything in an html comment
    let matches = [...source.toString().matchAll(re)];

    let embeddings = matches.map(m => { return { emb_ptr: m.groups.ptr.trim(), embedding: m.groups.emb.trim(), sourceIndex: m.index } })
    return embeddings;
}

async function findObjects(openrpcFile, embeddings) {
    try {

        let docToParse = await fileContentAsJSON(openrpcFile)
        let docToParseWithExternalRefs = await fetchExternalRefsFor(docToParse);
        let dereffedDoc = await derefAll(docToParseWithExternalRefs);

        let doc = await parseOpenRPCDocument(dereffedDoc)
        let resolvedRPCObjects = embeddings.map(emb => {
            let resolved = pointer.get(doc, emb.ref) //todo handle invalid pointers
            return { resolved, ...emb }
        })
        // console.log(JSON.stringify(resolvedRPCObjects))
        return resolvedRPCObjects;

    }
    catch (e) {
        console.error(e)
    }

}

async function embedRPCObject(mdFile, openrpcFile) {

    try {
        let mdSource = fs.readFileSync(mdFile);
        let embeddings = findRPCEmbeddings(mdSource)
            .map(e => parseEmbedding(e))
            .filter(e => e !== undefined);

        let rpcObjects = await findObjects(openrpcFile, embeddings)

        var out = mdSource.toString();
        rpcObjects.forEach(emb => {
            out = out.replace(emb.embedding, JSON.stringify(emb.resolved))
        })
        return out;
    }
    catch (e) {
        console.error(e.message || e.toString())
    }

}

//==========================================
let args = process.argv.slice(2);

if (args.length >= 2) {
    let mdFile = args[0];
    let openrpcFile = args[1];
    embedRPCObject(mdFile, openrpcFile)
        .then(result => console.info(result))
}
else {
    console.error("Invalid arguments")
}
