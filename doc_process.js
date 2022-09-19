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

const RPC_DOC_CACHE = {};

async function getDocFromFile(filename) {
    if (!filename) return null;
    if (!RPC_DOC_CACHE[filename])
        RPC_DOC_CACHE[filename] = await loadAndParseRPCDoc(filename);
    return RPC_DOC_CACHE[filename]
}

async function findObjects(embeddings) {
    try {
        let resolvedRPCObjects =
            Promise.all(
                embeddings.map(async emb => {
                    try {

                        let doc = await getDocFromFile(emb.filename);
                        let resolved = pointer.get(doc, emb.ref)
                        return { resolved, ...emb }
                    }
                    catch (err) {
                        // in case of some error for a given embedding, warn but skip it - don't stop everything.
                        console.warn(`Error: ${err.message || err.toString()}`)
                        return undefined;
                    }
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

        //start with the markdown source, and replace each embedding with the resolved object.
        return rpcObjects
            .filter(o => o !== undefined)
            .reduce(
                (outputSoFar, emb) => outputSoFar.replace(emb.embedding, JSON.stringify(emb.resolved)),
                mdSource.toString()
            )
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
