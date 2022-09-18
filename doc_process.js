#!/usr/bin/env node

const fs = require('fs-extra');
const { parseOpenRPCDocument } = require("@open-rpc/schema-utils-js");

const pointer = require('json-pointer');
const { fileContentAsJSON, derefAll, fetchExternalRefsFor } = require('./rpc_doc_utils')

function parseEmbedding(emb, defaultFilename) {

    let a = emb.emb_ptr.split(':')
    if (a.length < 2) return undefined;
    let qualifier = a[0];
    let filename = a.length >= 3 ? a[1] : defaultFilename;
    let ref = a.length >= 3 ? a[2] : a[1];
    // console.log(`Parsed embedding: q: ${qualifier}, f: ${filename}, r: ${ref}`)
    return { qualifier, ref, filename, ...emb }
}

function findRPCEmbeddings(source) {

    let re = /(?<emb><!--(?<ptr>[^\-\-\>]*)\-\-\>)/g //match and capture anything in an html comment
    let matches = [...source.toString().matchAll(re)];

    let embeddings = matches.map(m => { return { emb_ptr: m.groups.ptr.trim(), embedding: m.groups.emb.trim(), sourceIndex: m.index } })
    return embeddings;
}

async function loadAndParseRPCDoc(filename) {
    let docToParse = await fileContentAsJSON(filename)
    let docToParseWithExternalRefs = await fetchExternalRefsFor(docToParse);
    let dereffedDoc = await derefAll(docToParseWithExternalRefs);

    let doc = await parseOpenRPCDocument(dereffedDoc)
    return doc;
}

async function findObjects(embeddings) {
    try {
        let resolvedRPCObjects =
            Promise.all(
                embeddings.map(async emb => {
                    let doc = await loadAndParseRPCDoc(emb.filename);//todo: cache and reuse documents
                    let resolved = pointer.get(doc, emb.ref) //todo handle invalid pointers
                    return { resolved, ...emb }
                }))
        // console.log(JSON.stringify(resolvedRPCObjects))
        return resolvedRPCObjects;

    }
    catch (e) {
        console.error(e)
    }

}

async function embedRPCObjects(mdFile, defaultOpenrpcFile) {

    try {
        let mdSource = fs.readFileSync(mdFile);
        let embeddings = findRPCEmbeddings(mdSource)
            .map(e => parseEmbedding(e, defaultOpenrpcFile))
            .filter(e => e !== undefined);

        let rpcObjects = await findObjects(embeddings)

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
    let defaultOpenrpcFile = args[1];
    embedRPCObjects(mdFile, defaultOpenrpcFile)
        .then(result => console.info(result))
}
else {
    console.error("Invalid arguments")
}
