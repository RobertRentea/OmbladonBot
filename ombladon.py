import discord
import youtube_dl
import os
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(command_prefix = '!')
TOKEN = os.getenv('DISCORD_TOKEN')

players = {}

@bot.event
async def on_ready():
	print('Ombladon online')


@bot.command(pass_context=True)
async def join(ctx):
	channel = ctx.message.author.voice.channel
	if not channel:
		await ctx.send('You are not in a voice channel!')
		return
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	if voice and voice.is_connected():
		await voice.move_to(channel)
	else:
		voice = await channel.connect()
	await voice.disconnect()
	if voice and voice.is_connected():
		await voice.move_to(channel)
	else:
		voice = await channel.connect()
	await ctx.send(f'Joined {channel}')

@bot.command(pass_context=True)
async def play(ctx, url):
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	if not voice:
		await ctx.invoke(bot.get_command('join'))
	song_there = os.path.isfile('song.mp3')
	try:
		if song_there:
			os.remove('song.mp3')
	except PermissionError:
		await ctx.send('Wait for the current playing music end or use the \'stop\' command')
		return
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	ydl_opts = {
		'format': 'bestaudio/best',
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}],
	}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download([url])
	for file in os.listdir('./'):
		if file.endswith('.mp3'):
			os.rename(file, 'song.mp3')
	voice.play(discord.FFmpegPCMAudio('song.mp3'))
	voice.volume = 100
	voice.is_playing()

@bot.command(pass_context=True)
async def pause(ctx):
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	if voice and voice.is_playing():
		voice.pause()

@bot.command(pass_context=True)
async def resume(ctx):
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	if voice and voice.is_paused():
		voice.resume()

@bot.command(pass_context=True)
async def leave(ctx):
	channel = ctx.message.author.voice.channel
	voice = get(bot.voice_clients, guild=ctx.message.guild)
	if voice and voice.is_connected():
		await voice.disconnect()
		await ctx.send(f'Left {channel}')
	else:
		await ctx.send("Don't think I am in a voice channel")

bot.run(TOKEN)