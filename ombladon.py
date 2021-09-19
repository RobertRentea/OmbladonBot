import discord
import youtube_dl
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        async with ctx.typing():
            player  = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)

            self.queue.append(player)
            print(ctx.voice_client.is_playing())
            if len(self.queue) == 1 and ctx.voice_client.is_playing() is False:
                print('got here')
                self.start_playing(ctx.voice_client)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def next(self, ctx):
        ctx.voice_client.next()

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """Resumes the curent song"""

        ctx.voice_client.resume()

    @commands.command()
    async def next(self, ctx):
        del self.queue[0]

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot form voice channel"""

        await ctx.voice_client.disconnect()

    def start_playing(self, voice_client):
        while len(self.queue) > 0:
            player = self.queue[0]
            voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            self.queue.pop(0)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), 
                   description='Ombladon, the better Groovy')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.add_cog(Music(bot))
bot.run(TOKEN)