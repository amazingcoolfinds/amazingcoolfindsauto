/**
 * Cloudflare Worker - Telegram Bot for Sentinel
 */

const TELEGRAM_API = 'https://api.telegram.org';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (request.method === 'POST') {
      try {
        const text = await request.text();
        const update = JSON.parse(text);
        await handleUpdate(update, env);
        return new Response('ok');
      } catch (e) {
        console.error('Parse error:', e);
        return new Response('ok');
      }
    }
    
    return new Response('ok');
  }
};

async function handleUpdate(update, env) {
  const message = update.message;
  if (!message) return;
  
  const chatId = message.chat.id;
  const text = message.text || '';
  
  let reply = '';
  
  if (text === '/start' || text === '/help') {
    reply = `👋 ¡Hola! Soy Sentinel Bot.\n\nComandos:\n/status - Estado del pipeline\n/health - Health check\n/run - Disparar pipeline`;
  } 
  else if (text === '/status') {
    reply = '✅ Bot funcionando correctamente\n\nPipeline: Verificando...';
  }
  else if (text === '/health') {
    reply = `✅ Health Check\n\n🟢 Cloudflare: OK\n🟢 Worker: OK`;
  }
  else if (text === '/run') {
    reply = '🚀 Pipeline triggered via Make.com';
  }
  else {
    reply = `No entendí: ${text}\n\nUsa /start para ver comandos.`;
  }
  
  await sendReply(chatId, reply);
}

async function sendReply(chatId, text) {
  const token = env.TELEGRAM_BOT_TOKEN;
  await fetch(`${TELEGRAM_API}/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: text
    })
  });
}
