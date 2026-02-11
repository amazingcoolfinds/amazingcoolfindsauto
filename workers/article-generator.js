/**
 * Cloudflare Worker - AI Article Generator
 * Uses Workers AI to generate engaging blog articles
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Route: Generate Article (Manual trigger)
    if (url.pathname === '/api/generate-article' && request.method === 'POST') {
      try {
        const { topic, category, style } = await request.json();
        const article = await generateArticle(env.AI, topic, category, style);
        
        return new Response(JSON.stringify(article), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: List All Images (Debug)
    if (url.pathname === '/api/admin/list-images' && request.method === 'GET') {
      try {
        const list = await env.IMAGES.list();
        return new Response(JSON.stringify(list.objects.map(o => o.key)), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Clear All Articles (Admin reset)
    if (url.pathname === '/api/admin/clear-articles' && request.method === 'POST') {
      try {
        const list = await env.ARTICLES.list();
        for (const key of list.keys) {
          await env.ARTICLES.delete(key.name);
        }
        return new Response(JSON.stringify({ success: true, message: `Deleted ${list.keys.length} articles` }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Force Autonomous Run (For testing)
    if (url.pathname === '/api/admin/run-autonomous' && request.method === 'POST') {
      try {
        const result = await autonomousGeneration(env);
        return new Response(JSON.stringify(result), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Get All Articles
    if (url.pathname === '/api/articles' && request.method === 'GET') {
      try {
        const list = await env.ARTICLES.list();
        const articles = [];
        for (const key of list.keys) {
          if (key.name === 'featured_products') continue;
          const article = await env.ARTICLES.get(key.name);
          if (article) { articles.push(JSON.parse(article)); }
        }
        return new Response(JSON.stringify(articles), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Delete Article by Slug (Admin)
    if (url.pathname === '/api/admin/delete-article' && request.method === 'POST') {
      try {
        const { slug } = await request.json();
        const list = await env.ARTICLES.list();
        let deletedCount = 0;
        for (const key of list.keys) {
          const articleStr = await env.ARTICLES.get(key.name);
          if (articleStr) {
            const article = JSON.parse(articleStr);
            if (article.slug === slug || key.name === `article-${slug}`) {
              await env.ARTICLES.delete(key.name);
              deletedCount++;
            }
          }
        }
        return new Response(JSON.stringify({ success: true, deletedCount }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Get Featured Products
    if (url.pathname === '/api/products' && request.method === 'GET') {
      try {
        const products = await env.ARTICLES.get('featured_products');
        return new Response(products || '[]', {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Generate Featured Products (Admin)
    if (url.pathname === '/api/admin/generate-products' && request.method === 'POST') {
      try {
        const products = await generateFeaturedProducts(env.AI);
        await env.ARTICLES.put('featured_products', JSON.stringify(products));
        return new Response(JSON.stringify({ success: true, count: products.length }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Route: Serve Images from R2
    if (url.pathname.startsWith('/media/')) {
      const key = url.pathname.replace('/media/', '');
      const object = await env.IMAGES.get(key);
      
      if (!object) return new Response('Image not found', { status: 404 });
      
      const headers = new Headers();
      object.writeHttpMetadata(headers);
      headers.set('etag', object.httpEtag);
      headers.set('Cache-Control', 'public, max-age=31536000');
      headers.set('Access-Control-Allow-Origin', '*'); // CRITICAL: Allow images to load on website
      
      return new Response(object.body, { headers });
    }

    return new Response('Amazing Cool Finds API - Autonomous Mode Active', { headers: corsHeaders });
  },

  // CRON TRIGGER: This runs automatically every day
  async scheduled(event, env, ctx) {
    console.log("🚀 Starting daily autonomous run...");
    ctx.waitUntil(Promise.all([
      autonomousGeneration(env),
      generateFeaturedProducts(env.AI).then(products => env.ARTICLES.put('featured_products', JSON.stringify(products)))
    ]));
  }
};

/**
 * Autonomous Workflow
 */
async function selectDailyTrend(ai) {
  const categories = ['Tech', 'Gaming', 'Home', 'Lifestyle', 'Auto'];
  const category = categories[Math.floor(Math.random() * categories.length)];
  
  const prompt = `Generate ONE highly creative, punchy, and viral listicle title for "Amazing Cool Finds" in the ${category} category.
  
  CRITICAL RULES:
  1. AVOID CLICHES: Do NOT use "Never Knew Existed", "Revolutionizing Tomorrow", "Level Up", or "Game-Changing".
  2. VARY THE STRUCTURE: Don't always start with a number. Use questions, direct statements, or intriguing hooks.
  3. AUDIENCE: Tech-savvy, curious shoppers looking for "cool" and productive finds.
  4. LENGTH: Keep it under 65 characters.
  
  Format: JSON ONLY. 
  Example: {"topic": "Why Your Desk Setup Is Killing Your Productivity (And How to Fix It)", "category": "${category}"}`;

  const response = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
    messages: [{ role: 'user', content: prompt }]
  });

  try {
    const jsonStr = response.response.match(/\{.*\}/s)[0];
    return JSON.parse(jsonStr);
  } catch (e) {
    return { topic: `Best ${category} Finds of 2026`, category };
  }
}

async function autonomousGeneration(env) {
  const debug = { logs: [] };
  try {
    const trend = await selectDailyTrend(env.AI);
    const article = await generateArticle(env.AI, trend.topic, trend.category, 'engaging');
    
    // 1. GENERATE & STORE HERO IMAGE (Upgrading to FLUX-1-Schnell for premium realism)
    debug.logs.push(`Generating premium hero image with FLUX...`);
    try {
      const response = await env.AI.run('@cf/black-forest-labs/flux-1-schnell', {
        prompt: `Breathtaking high-end commercial photography, professional lifestyle blog layout, ${article.imagePrompt}. Warm natural lighting, editorial style, 8k resolution, photorealistic, sharp focus, clean composition, luxury aesthetic.`,
        num_steps: 4 
      });

      if (response && response.image) {
        // FLUX returns a Base64 string in an object
        const binaryString = atob(response.image);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        const heroKey = `hero-${article.slug}-${Date.now()}.png`;
        await env.IMAGES.put(heroKey, bytes, { httpMetadata: { contentType: 'image/png' } });
        
        // Hostname del Worker para servir las imágenes
        const workerOrigin = 'https://article-generator.amazingcoolfinds.workers.dev';
        
        article.r2_key = heroKey;
        article.image = `${workerOrigin}/media/${heroKey}`;
        article.isCloud = true; 
        
        debug.logs.push(`✅ AI Hero saved and URL synced: ${article.image}`);
      } else {
        debug.logs.push(`❌ Flux response missing image data`);
      }
    } catch(e) { 
      debug.logs.push(`❌ Flux Image failed: ${e.message}`); 
    }

    // 2. Save to KV
    const articleId = `article-${article.slug}-${Date.now()}`;
    await env.ARTICLES.put(articleId, JSON.stringify(article));

    // 3. AUTOMATE REDDIT POST
    try {
      const redditRes = await postToReddit(env, article);
      debug.logs.push(`Reddit Status: ${redditRes.success ? '✅ Posted' : '❌ Failed: ' + redditRes.error}`);
    } catch(e) {
      debug.logs.push(`❌ Reddit Error: ${e.message}`);
    }

    return { success: true, topic: trend.topic, articleId, debug };
  } catch (error) {
    return { success: false, error: error.message, debug };
  }
}

async function generateFeaturedProducts(ai) {
  const categories = ['Tech Gadgets', 'Home Essentials', 'Lifestyle Accessories', 'Automotive Gear'];
  const results = [];

  for (const cat of categories) {
    const prompt = `Suggest 2 literal, high-selling Amazon products in the ${cat} category for a premium blog "Amazing Cool Finds".
    Return JSON array ONLY: [{"title": "Short Item Name", "price": "$99", "asin": "B0...", "discount": "20% OFF", "category": "${cat}"}]`;

    const response = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7
    });

    try {
      const jsonStr = response.response.match(/\[.*\]/s)[0];
      const items = JSON.parse(jsonStr);
      for (const item of items) {
        results.push({
          ...item,
          affiliate_url: `https://www.amazon.com/dp/${item.asin}?tag=amazingcoolfinds-20`,
          image_url: `https://placehold.co/800x600/161616/FFD700.png?text=${encodeURIComponent(item.title)}`,
          images: [] // Carousel images placeholder
        });
      }
    } catch (e) { console.error("Item gen failed for " + cat); }
  }
  return results;
}

async function postToReddit(env, article) {
  // Check if we have credentials
  if (!env.REDDIT_CLIENT_ID || !env.REDDIT_SECRET || !env.REDDIT_USERNAME || !env.REDDIT_PASSWORD) {
    return { success: false, error: "Missing Reddit credentials in env" };
  }

  try {
    // 1. Get Access Token
    const auth = btoa(`${env.REDDIT_CLIENT_ID}:${env.REDDIT_SECRET}`);
    const tokenRes = await fetch('https://www.reddit.com/api/v1/access_token', {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'AmazingCoolFindsWorker/1.0 by ' + env.REDDIT_USERNAME
      },
      body: `grant_type=password&username=${env.REDDIT_USERNAME}&password=${env.REDDIT_PASSWORD}`
    });

    const tokenData = await tokenRes.json();
    if (!tokenData.access_token) return { success: false, error: "Failed to get access token" };

    // 2. Submit Text Post
    const articleUrl = `${env.WEBSITE_URL}/article.html?id=${article.slug}`;
    const fullBody = `${article.redditPost}\n\nRead more at: ${articleUrl}`;
    
    const submitRes = await fetch('https://oauth.reddit.com/api/submit', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'AmazingCoolFindsWorker/1.0 by ' + env.REDDIT_USERNAME
      },
      body: new URLSearchParams({
        sr: env.REDDIT_SUBREDDIT || 'test',
        kind: 'self',
        title: article.title,
        text: fullBody
      })
    });

    const result = await submitRes.json();
    return { success: true, data: result };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

async function generateProductsForTopic(ai, topic) {
  const prompt = `Suggest 3 real, specific Amazon products for: "${topic}". 
  Return JSON array ONLY: [{"name": "Product Name", "price": "$99", "review": "Concise review...", "asin": "B0XXXX"}]`;

  const response = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
    messages: [{ role: 'user', content: prompt }]
  });

  try {
    const jsonStr = response.response.match(/\[.*\]/s)[0];
    const products = JSON.parse(jsonStr);
    
    return products.map(p => ({
      ...p,
      affiliate_url: `https://www.amazon.com/s?k=${encodeURIComponent(p.name)}&tag=amazingcoolfinds-20`,
      // Use a more reliable image source for products
      image_url: `https://placehold.co/500x500/161616/FFD700.png?text=${encodeURIComponent(p.name)}`
    }));
  } catch (e) {
    return [];
  }
}

async function generateArticle(ai, topic, category = 'Tech', style = 'witty and engaging') {
  const prompts = {
    title: `Create a punchy, creative headline for an article about: ${topic}. 
    RULES: Avoid "Ultimate Guide" or "Best of". Be intriguing. Return ONLY the text.`,
    intro: `Write a compelling 2-paragraph introduction for ${topic}. 
    Tone: ${style}. Hook the reader immediately. 
    IMPORTANT: Start directly with the content. No "In this article..." filler.`,
    mainContent: `Write a detailed, high-quality article about ${topic}. 
      FORMAT RULES:
      1. Use exactly 5 sections starting with Markdown headers (###).
      2. Headers MUST be clickable Markdown links: ### [Product Name](https://www.amazon.com/s?k=Product+Name&tag=amazingcoolfinds-20)
      3. CRITICAL: No spaces between the ] and the (. Example: [Name](URL).
      4. Do NOT show the raw URL text, hide it behind the product name.`,
    conclusion: `Write a punchy closing paragraph for ${topic}. No "In conclusion" or "Summarizing".`,
    tags: `Generate 5 viral comma-separated tags for ${topic}.`,
    redditPost: `Write a Reddit-style post for the subreddit r/tech or r/homeautomation about ${topic}. 
    Style: Conversational, intriguing, maybe a bit controversial or helpful. 
    IMPORTANT: Do NOT include the link yet, just the body text.`
  };

  const [titleRaw, introRaw, mainContentRaw, conclusionRaw, tagsRaw, redditPostRaw] = await Promise.all([
    runAI(ai, prompts.title, 0.9), 
    runAI(ai, prompts.intro, 0.7),
    runAI(ai, prompts.mainContent, 0.5), 
    runAI(ai, prompts.conclusion, 0.7),
    runAI(ai, prompts.tags, 0.5),
    runAI(ai, prompts.redditPost, 0.8)
  ]);

  // Deep cleaning routine
  const clean = (text) => text.replace(/^(here is|based on|sure|according to|i have|suggested title).*?:/gi, '').trim();
  
  // REGEX FIREWALL: Fix malformed Markdown links in headers
  // Case 1: Header(URL) -> [Header](URL)
  let mainContent = clean(mainContentRaw);
  mainContent = mainContent.replace(/^###\s+([^(\[]+)\((https?:\/\/[^)]+)\)/gm, '### [$1]($2)');
  // Case 2: [Header] (URL) -> [Header](URL)
  mainContent = mainContent.replace(/\]\s+\(/g, '](');
  
  const title = clean(titleRaw.split('\n')[0]).replace(/^["']|["']$/g, '').substring(0, 100);
  const intro = clean(introRaw);
  const conclusion = clean(conclusionRaw);

  const slug = slugify(title);
  const imagePrompt = `Epic high-end lifestyle photography, ${category} concept, ${title}, cinematic lighting, 8k`;

  return {
    title,
    slug,
    category,
    intro,
    content: mainContent,
    conclusion,
    metaDescription: intro.substring(0, 150) + '...',
    tags: tagsRaw.split(',').map(t => t.trim().replace(/[^a-zA-Z0-9 ]/g, '')),
    imagePrompt,
    redditPost: redditPostRaw,
    createdAt: new Date().toISOString(),
    readTime: estimateReadTime(mainContent),
    products: []
  };
}

async function runAI(ai, prompt, temperature = 0.5) {
  const response = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
    messages: [
      { role: 'system', content: 'You are a robotic content generator. You never use conversational filler like "Sure," "Here is," or "Okay." You provide only the requested text content.' },
      { role: 'user', content: prompt }
    ],
    max_tokens: 1500,
    temperature: temperature
  });

  return response.response || '';
}

/**
 * Create URL-friendly slug
 */
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
    .substring(0, 80); // Strict limit for KV keys
}

/**
 * Estimate reading time
 */
function estimateReadTime(text) {
  const wordsPerMinute = 200;
  const wordCount = text.split(/\s+/).length;
  const minutes = Math.ceil(wordCount / wordsPerMinute);
  return `${minutes} min read`;
}
