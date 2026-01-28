import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# --- 🌐 RENDER 7/24 AKTİF TUTMA SİSTEMİ ---
app = Flask('')
@app.route('/')
def home():
    return "Bot Aktif! 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 🔴 AYARLAR ---
TOKEN = os.getenv('TOKEN') 
KAYITLI_ROL_ID = 1253327741063794771
KAYITSIZ_ROL_ID = 1253313874342711337
BASVURULAR_KATEGORI_ADI = "Başvurular"

# Yetki başvurularını görecek olan roller
YETKILI_ROLLER = [
    1253285883826929810, 
    1465050726576427263, 
    1465056480871845949
]

# --- 🔒 BAŞVURU KANALI KAPATMA BUTONU ---
class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Başvuruyu Kapat & Sil", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_kapat")
    async def kapat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kanal 5 saniye içinde siliniyor...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- 📝 YETKİ BAŞVURU FORMU (MODAL) ---
class YetkiBasvuruModal(discord.ui.Modal, title='Admin Başvuru Formu'):
    isim_yas = discord.ui.TextInput(label='İsim ve Yaşınız', placeholder='Örn: Ahmet, 20', required=True)
    sure = discord.ui.TextInput(label='Sunucudaki süreniz?', placeholder='Örn: 3 Ay', required=True)
    komut = discord.ui.TextInput(label='Adminlik komutlarını biliyor musunuz?', placeholder='Evet/Hayır', required=True)
    steam = discord.ui.TextInput(label='Steam Profil Linkiniz', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=BASVURULAR_KATEGORI_ADI)
        
        if not category:
            return await interaction.response.send_message(f"❌ '{BASVURULAR_KATEGORI_ADI}' kategorisi bulunamadı!", ephemeral=True)

        num = len([c for c in guild.channels if c.name.startswith("basvuru-")]) + 1
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for r_id in YETKILI_ROLLER:
            role = guild.get_role(r_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"basvuru-{num}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title=f"Yeni Yetki Başvurusu #{num}", color=discord.Color.blue())
        embed.add_field(name="Aday", value=interaction.user.mention)
        embed.add_field(name="İsim/Yaş", value=self.isim_yas.value)
        embed.add_field(name="Süre", value=self.sure.value)
        embed.add_field(name="Komut Bilgisi", value=self.komut.value)
        embed.add_field(name="Steam", value=self.steam.value, inline=False)
        
        yetkili_mention = " ".join([f"<@&{rid}>" for rid in YETKILI_ROLLER])
        await channel.send(content=yetkili_mention, embed=embed, view=TicketKapatView())
        await interaction.response.send_message(f"✅ Başvurunuz alındı: {channel.mention}", ephemeral=True)

# --- 🔘 ANA MENÜ ---
class AnaMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Admin Başvuru", style=discord.ButtonStyle.success, emoji="📩", custom_id="btn_admin")
    async def admin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(YetkiBasvuruModal())

# --- 🤖 BOT SINIFI ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f'{self.user} hazır ve 7/24 aktif!')
        self.add_view(AnaMenu())
        self.add_view(TicketKapatView())

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def sistem_kur(ctx):
    embed = discord.Embed(
        title="Admin Başvuru Paneli", 
        description="Yetki başvurusunda bulunmak için aşağıdaki butona tıklayın.", 
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=AnaMenu())

@bot.command()
async def kayıt(ctx, isim=None, yas=None):
    if not isim or not yas:
        return await ctx.send("❗ Kullanım: `!kayıt İsim Yaş` ")
    
    try:
        await ctx.author.edit(nick=f"{isim} | {yas}")
        await ctx.author.add_roles(ctx.guild.get_role(KAYITLI_ROL_ID))
        await ctx.author.remove_roles(ctx.guild.get_role(KAYITSIZ_ROL_ID))
        await ctx.send(f"✅ Hoş geldin **{isim}**, kaydın yapıldı!")
    except Exception as e:
        await ctx.send("❌ Yetki hatası: Botun rolü en üstte olmalı.")

keep_alive()
bot.run(TOKEN)