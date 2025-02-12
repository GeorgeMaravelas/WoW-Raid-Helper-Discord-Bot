import discord
from discord.ext import commands
import json
import os

# Replace with your bot token
TOKEN = "hmm"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

roles = {
    "Tank": ["Warrior", "Demon Hunter"],
    "Healer": ["Paladin", "Priest"],
    "DPS": ["Rogue", "Shaman"]
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"user_roles": {}, "user_specializations": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

class SpecializationView(discord.ui.View):

    def __init__(self, user_id, role):
        super().__init__()
        self.user_id = str(user_id)
        self.role = role

        for spec in roles[role]:
            self.add_item(SpecializationButton(self.user_id, self.role, spec))

class SpecializationButton(discord.ui.Button):
    
    def __init__(self, user_id, role, specialization):
        super().__init__(label=specialization, style=discord.ButtonStyle.primary)
        self.user_id = user_id
        self.role = role
        self.specialization = specialization

    async def callback(self, interaction: discord.Interaction):
        """Specialization selection."""
        if self.user_id not in data["user_specializations"]:
            data["user_specializations"][self.user_id] = {}
        
        data["user_specializations"][self.user_id][self.role] = self.specialization
        save_data()
        await interaction.response.edit_message(content=f"✅ You have selected **{self.specialization}** as your {self.role}.", view=None)

class RoleSelectionView(discord.ui.View):

    def __init__(self, title="Role Assignments", description="View who has signed up for each role."):
        super().__init__()
        self.title = title
        self.description = description

    async def update_message(self, interaction):
        """current members under each role."""
        
        role_lists = {
            "Tank": [],
            "Healer": [],
            "DPS": []
        }

        for user_id, role in data["user_roles"].items():
            specialization = data["user_specializations"].get(user_id, {}).get(role, "No specialization")
            user = await bot.fetch_user(int(user_id))
            server_name = user.display_name  # Get the nickname or username
            role_lists[role].append(f"{server_name} - {specialization}")

        # fields for each role
        embed = discord.Embed(title=self.title, description=self.description, color=discord.Color.blue())

        # Tank list
        tank_list = "\n".join(role_lists["Tank"]) if role_lists["Tank"] else "No one signed up yet."
        embed.add_field(name="**Tank**", value=tank_list, inline=True)

        # Healer list
        healer_list = "\n".join(role_lists["Healer"]) if role_lists["Healer"] else "No one signed up yet."
        embed.add_field(name="**Healer**", value=healer_list, inline=True)

        # DPS list
        dps_list = "\n".join(role_lists["DPS"]) if role_lists["DPS"] else "No one signed up yet."
        embed.add_field(name="**DPS**", value=dps_list, inline=True)

        await interaction.response.edit_message(embed=embed, view=self)

    async def handle_choice(self, interaction, role):
        """Handles role selection and asks for specialization if needed."""
        user_id = str(interaction.user.id)  # Convert to string for JSON keys

        data["user_roles"][user_id] = role
        save_data()

        await self.update_message(interaction)

        if user_id not in data["user_specializations"] or role not in data["user_specializations"][user_id]:
            await interaction.followup.send(
                f"🛠️ Please choose your specialization for **{role}**:",
                view=SpecializationView(user_id, role),
                ephemeral=True
            )

    @discord.ui.button(label="Tank", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def tank_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "Tank")

    @discord.ui.button(label="Healer", style=discord.ButtonStyle.primary, emoji="✨")
    async def healer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "Healer")

    @discord.ui.button(label="DPS", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def dps_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "DPS")

@bot.command()
async def start(ctx, *, args=None):
    title = "Role Assignments"
    description = "View who has signed up for each role."
    
    if args:
        parts = args.split(" | ")
        if len(parts) == 2:
            title, description = parts
        else:
            await ctx.send('Please provide both a title and description, separated by " | ".\n Example: !start "Wont happen again (bolvar probably)" | "If I die once, I die twice" selections!')
            return

    view = RoleSelectionView(title=title, description=description)
    await ctx.send("Click a button to select your role!", view=view)

bot.run(TOKEN)