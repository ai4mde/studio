const express = require('express');
const puppeteer = require('puppeteer-core');
const url = require('url');

const PORT = 3000;
const api = express();

let browser;

async function startBrowser() {
    return await puppeteer.launch({
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--no-zygote',
            '--single-process',
            '--disable-features=IsolateOrigins,site-per-process',
        ],
        headless: true,
    });
}

async function generateSVG(diagram_id) {
    console.log('Generating SVG for diagram:', diagram_id);
    const pageUrl = `http://ai4mde.localhost/diagram/${diagram_id}`;

    const page = await browser.newPage();
    try {
        await page.goto(pageUrl, { waitUntil: 'networkidle0' });

        const loginFormPresent = await page.$('input[name=username]') && await page.$('input[name=password]');
        if (loginFormPresent) {
            await page.evaluate((username, password) => {
                document.querySelector('input[name=username]').value = username;
                document.querySelector('input[name=password]').value = password;
            }, process.env.DJANGO_SUPERUSER_USERNAME, process.env.DJANGO_SUPERUSER_PASSWORD);

            await page.click('button[name=login]');
            await page.waitForSelector('main');
            await new Promise(resolve => setTimeout(resolve, 2000));
        } else {
            console.log('Login form not present, skipping authentication.');
            await page.waitForSelector('main');
        }

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

        await new Promise(resolve => setTimeout(resolve, 1000));

        if (svgResult) {
            const rawSVG = decodeURIComponent(svgResult.split(',')[1]);
            console.log('Successfully generated SVG for diagram:', diagram_id);
            return rawSVG;
        } else {
            throw new Error('SVG generation failed');
        }
    } finally {
        await page.close();
    }
}

api.get('/svg', async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const diagram_id = parsedUrl.query.diagram_id;

    if (!diagram_id) {
        res.statusCode = 400;
        res.setHeader('Content-Type', 'text/plain');
        res.end('Missing "diagram_id" parameter\n');
        return;
    }

    try {
        const svgResult = await generateSVG(diagram_id);
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/plain');
        res.end(svgResult);
    } catch (error) {
        console.error('Error executing Puppeteer:', error);
        res.statusCode = 500;
        res.setHeader('Content-Type', 'text/plain');
        res.end('Internal Server Error');
    }
});

(async () => {
    try {
        browser = await startBrowser();
        const page = await browser.newPage();
        try {
            await page.goto("http://ai4mde.localhost", { waitUntil: 'networkidle0' });
            await page.evaluate((username, password) => {
                document.querySelector('input[name=username]').value = username;
                document.querySelector('input[name=password]').value = password;
            }, process.env.DJANGO_SUPERUSER_USERNAME, process.env.DJANGO_SUPERUSER_PASSWORD);
            await page.click('button[name=login]');
        } catch (error) {
            console.error('Authentication failed:', error);
        }
        api.listen(PORT, () => {
            console.log(`Running SVG server on http://localhost:${PORT}`);
        });
    } catch (error) {
        console.error('Error starting Puppeteer browser:', error);
        process.exit(1);
    }
})();

process.on('SIGINT', async () => {
    console.log('Shutting down server...');
    if (browser) {
        await browser.close();
        console.log('Browser closed');
    }
    process.exit(0);
});
