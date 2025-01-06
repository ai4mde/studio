const express = require('express')
const puppeteer = require('puppeteer-core');
const url = require('url');

const PORT = 3000
const api = express()

async function generateSVG(diagram_id) {
    console.log('Generating SVG for diagram:', diagram_id);
    const url = `http://studio:5173/diagram/${diagram_id}`;
    const browser = await puppeteer.launch({
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--no-zygote',
            '--single-process',
        ],
        headless: true,
    });
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle0' });

    await page.$eval('input[name=username]', el => el.value = process.env.DJANGO_SUPERUSER_USERNAME);
    await page.$eval('input[name=password]', el => el.value = process.env.DJANGO_SUPERUSER_PASSWORD);
    await page.click('button[name=login]');
    await page.waitForSelector('main');
    await new Promise(resolve => setTimeout(resolve, 2000));

    let svgResult = null;
    await page.exposeFunction('captureSVG', svg => {
        svgResult = svg;
    });

    await page.evaluate(() => {
        window.postMessage({ type: "generate-svg" }, window.origin);
        window.addEventListener("message", event => {
            if (event.data?.type === "svg-generated") {
                window.captureSVG(event.data.svg);
            }
        });
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    if (svgResult) {
        const rawSVG = decodeURIComponent(svgResult.split(',')[1]);
        await browser.close();
        console.log('Successfully generated SVG for diagram:', diagram_id);
        return rawSVG;
    } else {
        await browser.close();
        throw new Error('SVG generation failed');
    }
}

api.get('/svg', async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const diagram_id = parsedUrl.query.diagram_id;

    if (!diagram_id) {
        res.statusCode = 400;
        res.setHeader('Content-Type', 'text/plain');
        res.end('Missing "diagram_id" parameter\n');
        return
    }

    try {
        const svgResult = await generateSVG(diagram_id);
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/plain');
        res.end({
            'diagram_id': diagram_id,
            'svg': svgResult
        });
        return
    } catch (error) {
        console.error('Error executing Puppeteer:', error);
        res.statusCode = 500;
        res.setHeader('Content-Type', 'text/plain');
        res.end('Internal Server Error');
        return
    }

})

api.listen(PORT)
console.log(`Running SVG server on http://localhost:${PORT}`)
