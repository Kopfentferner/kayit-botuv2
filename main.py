import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# --- 🌐 RENDER 7/24 ---
app = Flask('')
@app.route('/')
def home():
    return "Bot Aktif 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# --- 🔴 AYARLAR ---
TOKEN = os.getenv("TOKEN")

BASVURULAR_KATEGORI_ADI = "Başvurular"

YETKILI_ROLLER = [
    1253285883826929810,
    1465050726576427263,
    1465056480871845949
]

# --- 🔒 KANAL KAPATMA BUTONU ---
class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Başvuruyu Kapat & Sil",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="btn_kapat"
    )
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "⏳ Kanal 5 saniye içinde siliniyor...",
            ephemeral=True
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- 📝 ADMIN BAŞVURU MODAL ---
class AdminBasvuruModal(discord.ui.Modal, title="Admin Başvuru Formu"):
    isim_yas = discord.ui.TextInput(label="İsim / Yaş", required=True)
    sure = discord.ui.TextInput(label="Sunucudaki Süreniz", required=True)
    bilgi = discord.ui.TextInput(label="Adminlik bilginiz var mı?", required=True)
    steam = discord.ui.TextInput(label="Steam Profil Linki", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await basvuru_kanali_olustur(
            interaction,
            "admin",
            {
                "İsim / Yaş": self.isim_yas.value,
                "Sunucu Süresi": self.sure.value,
                "Admin Bilgisi": self.bilgi.value,
                "Steam": self.steam.value
            }
        )

# --- 💎 VIP BAŞVURU MODAL ---
class VIPBasvuruModal(discord.ui.Modal, title="VIP Başvuru Formu"):
    isim = discord.ui.TextInput(label="İsim", required=True)
    yas = discord.ui.TextInput(label="Yaş", required=True)
    neden = discord.ui.TextInput(
        label="Neden VIP olmak istiyorsunuz?",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await basvuru_kanali_olustur(
            interaction,
            "vip",
            {
                "İsim": self.isim.value,
                "Yaş": self.yas.value,
                "Başvuru Nedeni": self.neden.value
            }
        )

# --- 📂 ORTAK KANAL OLUŞTURMA FONKSİYONU ---
async def basvuru_kanali_olustur(interaction, tur, alanlar):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name=BASVURULAR_KATEGORI_ADI)

    if not category:
        return await interaction.response.send_message(
            f"❌ `{BASVURULAR_KATEGORI_ADI}` kategorisi bulunamadı!",
            ephemeral=True
        )

    num = len([c for c in guild.channels if c.name.startswith(f"{tur}-basvuru")]) + 1

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    for rid in YETKILI_ROLLER:
        role = guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=f"{tur}-basvuru-{num}",
        category=category,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title=f"📌 Yeni {tur.upper()} Başvurusu",
        color=discord.Color.gold() if tur == "vip" else discord.Color.blue()
    )

    embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)

    for k, v in alanlar.items():
        embed.add_field(name=k, value=v, inline=False)

    yetkili_ping = " ".join([f"<@&{r}>" for r in YETKILI_ROLLER])

    await channel.send(
        content=yetkili_ping,
        embed=embed,
        view=TicketKapatView()
    )

    await interaction.response.send_message(
        f"✅ Başvurun alındı: {channel.mention}",
        ephemeral=True
    )

# --- 🔘 ANA PANEL ---
class AnaMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Admin Başvuru", style=discord.ButtonStyle.success, emoji="🛡️")
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminBasvuruModal())

    @discord.ui.button(label="VIP Başvuru", style=discord.ButtonStyle.primary, emoji="💎")
    async def vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VIPBasvuruModal())

# --- 🤖 BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"{self.user} aktif!")
        self.add_view(AnaMenu())
        self.add_view(TicketKapatView())

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def sistem_kur(ctx):
    embed = discord.Embed(
        title="📋 Başvuru Paneli",
        description=(
            "🛡️ **Admin Başvuru** → Özel kanal açılır\n"
            "💎 **VIP Başvuru** → Özel kanal açılır"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=AnaMenu())

keep_alive()
bot.run(TOKEN)
