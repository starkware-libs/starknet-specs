#!/usr/bin/env node

var fs = require('fs');

async function formatFile(filename) {
    try {

        const rawData = fs.readFileSync(filename, 'utf8');
        const jsonData = JSON.parse(rawData);
        const formattedData = JSON.stringify(jsonData, null, 2);
        fs.writeFileSync(filename, `${formattedData}\n`, 'utf8');
        console.log(filename, "formatted")

    } catch (error) {
        console.error(`Error processing file "${filename}":`, error);
    }


}


let args = process.argv.slice(2);

if (args.length > 0) {
    formatFile(args[0]);
} else console.error("Missing filename");