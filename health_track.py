import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta

class HealthTrackingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('health_data.db')
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS health_profiles
                     (user_id INTEGER PRIMARY KEY, is_public INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sleep_entries
                     (id INTEGER PRIMARY KEY, user_id INTEGER, hours_slept REAL, score INTEGER, 
                     description TEXT, bed_time TEXT, wake_time TEXT, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS diet_entries
                     (id INTEGER PRIMARY KEY, user_id INTEGER, food TEXT, calories INTEGER, 
                     protein REAL, fat REAL, carbs REAL, fiber REAL, date TEXT, time TEXT, description TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS exercise_entries
                     (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, reps INTEGER, sets INTEGER, 
                     variation TEXT, cool_down TEXT, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS todo_entries
                     (id INTEGER PRIMARY KEY, user_id INTEGER, task TEXT, date TEXT, completed INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS journal_entries
                     (id INTEGER PRIMARY KEY, user_id INTEGER, entry TEXT, date TEXT, time TEXT, mood INTEGER)''')
         c.execute('''CREATE TABLE IF NOT EXISTS body_tracking
                     (id INTEGER PRIMARY KEY, user_id INTEGER, mass_in_kg REAL, height REAL, 
                     age INTEGER, activity_level INTEGER, body_fat_percentage REAL, 
                     time TEXT, date TEXT)''')
        self.conn.commit()

    @app_commands.command(name="health_profile", description="Set or view health profile")
    @app_commands.describe(
        action="Choose 'set' to update your profile or 'view' to see a profile",
        is_public="Set your profile to public or private",
        user="The user whose profile to view (if public)"
    )
    async def health_profile(self, interaction: discord.Interaction, action: str, is_public: bool = None, user: discord.Member = None):
        if action == "set":
            if is_public is None:
                await interaction.response.send_message("Please specify whether your profile should be public or private.")
                return
            c = self.conn.cursor()
            c.execute("INSERT OR REPLACE INTO health_profiles (user_id, is_public) VALUES (?, ?)", (interaction.user.id, int(is_public)))
            self.conn.commit()
            await interaction.response.send_message(f"Your health profile has been set to {'public' if is_public else 'private'}.")
        elif action == "view":
            if user and user != interaction.user:
                c = self.conn.cursor()
                c.execute("SELECT is_public FROM health_profiles WHERE user_id = ?", (user.id,))
                result = c.fetchone()
                if not result or not result[0]:
                    await interaction.response.send_message("This user's health profile is private or doesn't exist.")
                    return
            target_user = user or interaction.user
            await self.show_health_profile(interaction, target_user)
        else:
            await interaction.response.send_message("Invalid action. Please use 'set' or 'view'.")

    async def show_health_profile(self, interaction: discord.Interaction, user: discord.Member):
        c = self.conn.cursor()
        
        # Fetch the latest entries for each category
        c.execute("SELECT * FROM sleep_entries WHERE user_id = ? ORDER BY date DESC LIMIT 1", (user.id,))
        sleep_entry = c.fetchone()
        
        c.execute("SELECT * FROM diet_entries WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", (user.id,))
        diet_entry = c.fetchone()
        
        c.execute("SELECT * FROM exercise_entries WHERE user_id = ? ORDER BY date DESC LIMIT 1", (user.id,))
        exercise_entry = c.fetchone()
        
        embed = discord.Embed(title=f"Health Profile for {user.display_name}", color=discord.Color.green())
        
        if sleep_entry:
            embed.add_field(name="Latest Sleep Entry", value=f"Date: {sleep_entry[7]}\nHours: {sleep_entry[2]}\nScore: {sleep_entry[3]}/5", inline=False)
        
        if diet_entry:
            embed.add_field(name="Latest Diet Entry", value=f"Date: {diet_entry[8]}\nFood: {diet_entry[2]}\nCalories: {diet_entry[3]}", inline=False)
        
        if exercise_entry:
            embed.add_field(name="Latest Exercise Entry", value=f"Date: {exercise_entry[7]}\nExercise: {exercise_entry[2]}\nSets: {exercise_entry[4]}, Reps: {exercise_entry[3]}", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sleep_track", description="Track your sleep")
    async def sleep_track(self, interaction: discord.Interaction):
        modal = SleepTrackingModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="diet_track", description="Track your diet")
    async def diet_track(self, interaction: discord.Interaction):
        modal = DietTrackingModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="exercise_track", description="Track your exercise")
    async def exercise_track(self, interaction: discord.Interaction):
        modal = ExerciseTrackingModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="todo", description="Manage your todo list")
    @app_commands.describe(
        action="Choose 'view', 'add', 'remove', or 'edit'",
        date="Date for the todo list (format: dd/mm/yyyy, or 'today', 'tomorrow', 'yesterday')"
    )
    async def todo(self, interaction: discord.Interaction, action: str, date: str = "today"):
        if action == "view":
            await self.view_todo(interaction, date)
        elif action == "add":
            modal = TodoAddModal(date)
            await interaction.response.send_modal(modal)
        elif action == "remove":
            modal = TodoRemoveModal(date)
            await interaction.response.send_modal(modal)
        elif action == "edit":
            modal = TodoEditModal(date)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Invalid action. Please use 'view', 'add', 'remove', or 'edit'.")

    async def view_todo(self, interaction: discord.Interaction, date: str):
        target_date = self.parse_date(date)
        c = self.conn.cursor()
        c.execute("SELECT task, completed FROM todo_entries WHERE user_id = ? AND date = ? ORDER BY id", (interaction.user.id, target_date.strftime("%Y-%m-%d")))
        todos = c.fetchall()

        if not todos:
            await interaction.response.send_message(f"No todos found for {target_date.strftime('%d/%m/%Y')}.")
            return

        embed = discord.Embed(title=f"Todo List for {target_date.strftime('%d/%m/%Y')}", color=discord.Color.blue())
        for i, (task, completed) in enumerate(todos, 1):
            status = "✅" if completed else "❌"
            embed.add_field(name=f"Task {i}", value=f"{status} {task}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="journal", description="Manage your journal entries")
    @app_commands.describe(
        action="Choose 'entry' to add a new entry or 'view' to see an entry",
        date="Date for viewing a specific entry (format: dd/mm/yyyy)"
    )
    async def journal(self, interaction: discord.Interaction, action: str, date: str = None):
        if action == "entry":
            modal = JournalEntryModal()
            await interaction.response.send_modal(modal)
        elif action == "view":
            if date:
                target_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
            else:
                c = self.conn.cursor()
                c.execute("SELECT date FROM journal_entries WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 1", (interaction.user.id,))
                result = c.fetchone()
                if result:
                    target_date = result[0]
                else:
                    await interaction.response.send_message("No journal entries found.")
                    return

            c = self.conn.cursor()
            c.execute("SELECT entry, time, mood FROM journal_entries WHERE user_id = ? AND date = ? ORDER BY time DESC LIMIT 1", (interaction.user.id, target_date))
            entry = c.fetchone()

            if entry:
                embed = discord.Embed(title=f"Journal Entry for {datetime.strptime(target_date, '%Y-%m-%d').strftime('%d/%m/%Y')}", color=discord.Color.purple())
                embed.add_field(name="Time", value=entry[1], inline=False)
                embed.add_field(name="Mood", value=f"{entry[2]}/5", inline=False)
                embed.add_field(name="Entry", value=entry[0], inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"No journal entry found for {datetime.strptime(target_date, '%Y-%m-%d').strftime('%d/%m/%Y')}.")
        else:
            await interaction.response.send_message("Invalid action. Please use 'entry' or 'view'.")

		@app_commands.command(name="body_track", description="Track your body measurements")
    async def body_track(self, interaction: discord.Interaction):
        modal = BodyTrackingModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="export_data", description="Export your health data as CSV")
    @app_commands.describe(
        data_type="Choose the type of data to export (sleep, diet, exercise, todo, journal, body)"
    )
    async def export_data(self, interaction: discord.Interaction, data_type: str):
        await interaction.response.defer(ephemeral=True)
        
        if data_type not in ["sleep", "diet", "exercise", "todo", "journal", "body"]:
            await interaction.followup.send("Invalid data type. Please choose from sleep, diet, exercise, todo, journal, or body.")
            return

        c = self.conn.cursor()
        if data_type == "sleep":
            c.execute("SELECT * FROM sleep_entries WHERE user_id = ?", (interaction.user.id,))
        elif data_type == "diet":
            c.execute("SELECT * FROM diet_entries WHERE user_id = ?", (interaction.user.id,))
        elif data_type == "exercise":
            c.execute("SELECT * FROM exercise_entries WHERE user_id = ?", (interaction.user.id,))
        elif data_type == "todo":
            c.execute("SELECT * FROM todo_entries WHERE user_id = ?", (interaction.user.id,))
        elif data_type == "journal":
            c.execute("SELECT * FROM journal_entries WHERE user_id = ?", (interaction.user.id,))
        elif data_type == "body":
            c.execute("SELECT * FROM body_tracking WHERE user_id = ?", (interaction.user.id,))

        rows = c.fetchall()
        if not rows:
            await interaction.followup.send(f"No {data_type} data found to export.")
            return

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([description[0] for description in c.description])  # Write headers
        writer.writerows(rows)

        output.seek(0)
        file = discord.File(fp=output, filename=f"{data_type}_data.csv")
        
        try:
            await interaction.user.send(f"Here's your exported {data_type} data:", file=file)
            await interaction.followup.send(f"Your {data_type} data has been sent to your DMs.")
        except discord.errors.Forbidden:
            await interaction.followup.send("I couldn't send you a DM. Please make sure your DM settings allow messages from server members.")

    @app_commands.command(name="visualize_data", description="Visualize your health data")
    @app_commands.describe(
        data_type="Choose the type of data to visualize (sleep, diet, exercise, body)",
        days="Number of days to include in the visualization (default: 30)"
    )
    async def visualize_data(self, interaction: discord.Interaction, data_type: str, days: int = 30):
        await interaction.response.defer(ephemeral=True)
        
        if data_type not in ["sleep", "diet", "exercise", "body"]:
            await interaction.followup.send("Invalid data type. Please choose from sleep, diet, exercise, or body.")
            return

        c = self.conn.cursor()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        if data_type == "sleep":
            c.execute("SELECT date, hours_slept, score FROM sleep_entries WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
                      (interaction.user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            df = pd.DataFrame(c.fetchall(), columns=["date", "hours_slept", "score"])
            df['date'] = pd.to_datetime(df['date'])
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
            sns.lineplot(data=df, x="date", y="hours_slept", ax=ax1)
            ax1.set_title("Sleep Duration Over Time")
            ax1.set_ylabel("Hours Slept")
            
            sns.lineplot(data=df, x="date", y="score", ax=ax2)
            ax2.set_title("Sleep Quality Score Over Time")
            ax2.set_ylabel("Score")

        elif data_type == "diet":
            c.execute("SELECT date, calories FROM diet_entries WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
                      (interaction.user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            df = pd.DataFrame(c.fetchall(), columns=["date", "calories"])
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby("date").sum().reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=df, x="date", y="calories", ax=ax)
            ax.set_title("Daily Calorie Intake")
            ax.set_ylabel("Calories")
            plt.xticks(rotation=45)

        elif data_type == "exercise":
            c.execute("SELECT date, name, sets * reps AS total_reps FROM exercise_entries WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
                      (interaction.user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            df = pd.DataFrame(c.fetchall(), columns=["date", "exercise", "total_reps"])
            df['date'] = pd.to_datetime(df['date'])
            
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.scatterplot(data=df, x="date", y="total_reps", hue="exercise", size="total_reps", sizes=(20, 200), ax=ax)
            ax.set_title("Exercise Progress Over Time")
            ax.set_ylabel("Total Reps")
            plt.xticks(rotation=45)

        elif data_type == "body":
            c.execute("SELECT date, mass_in_kg, body_fat_percentage FROM body_tracking WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
                      (interaction.user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            df = pd.DataFrame(c.fetchall(), columns=["date", "mass_in_kg", "body_fat_percentage"])
            df['date'] = pd.to_datetime(df['date'])
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
            sns.lineplot(data=df, x="date", y="mass_in_kg", ax=ax1)
            ax1.set_title("Body Mass Over Time")
            ax1.set_ylabel("Mass (kg)")
            
            sns.lineplot(data=df, x="date", y="body_fat_percentage", ax=ax2)
            ax2.set_title("Body Fat Percentage Over Time")
            ax2.set_ylabel("Body Fat %")

        plt.tight_layout()
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png')
        img_stream.seek(0)
        file = discord.File(fp=img_stream, filename="visualization.png")
        
        await interaction.followup.send(f"Here's your {data_type} data visualization:", file=file)

    @app_commands.command(name="calculate_tdee", description="Calculate your Total Daily Energy Expenditure")
    async def calculate_tdee(self, interaction: discord.Interaction):
        c = self.conn.cursor()
        c.execute("SELECT mass_in_kg, height, age, activity_level, body_fat_percentage FROM body_tracking WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                  (interaction.user.id,))
        result = c.fetchone()

        if not result:
            await interaction.response.send_message("Please track your body measurements first using the /body_track command.")
            return

        mass, height, age, activity_level, body_fat = result
        
        # Calculate Basal Metabolic Rate (BMR) using the Katch-McArdle formula
        lean_body_mass = mass * (1 - (body_fat / 100))
        bmr = 370 + (21.6 * lean_body_mass)
        
        # Calculate TDEE based on activity level
        activity_multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
        tdee = bmr * activity_multipliers[activity_level - 1]

        embed = discord.Embed(title="TDEE Calculation Results", color=discord.Color.green())
        embed.add_field(name="Basal Metabolic Rate (BMR)", value=f"{bmr:.2f} calories", inline=False)
        embed.add_field(name="Total Daily Energy Expenditure (TDEE)", value=f"{tdee:.2f} calories", inline=False)
        embed.set_footer(text="TDEE is an estimate and may vary based on individual factors.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="health_help", description="Display help for health tracking commands")
    async def health_help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Health Tracking Commands", color=discord.Color.blue())
        embed.add_field(name="/health_profile", value="Set or view health profiles. Use 'set' to update your profile visibility, or 'view' to see profiles.", inline=False)
        embed.add_field(name="/sleep_track", value="Track your sleep. Input hours slept, score, description, bed time, and wake-up time.", inline=False)
        embed.add_field(name="/diet_track", value="Track your diet. Input food, calories, protein, fat, carbs, fiber, date, time, and description.", inline=False)
        embed.add_field(name="/exercise_track", value="Track your exercises. Input name, reps, sets, variation/weights, cool-down, and date.", inline=False)
        embed.add_field(name="/todo", value="Manage your todo list. Use 'view', 'add', 'remove', or 'edit' actions. Specify dates as needed.", inline=False)
        embed.add_field(name="/journal", value="Manage your journal. Use 'entry' to add a new entry or 'view' to see entries. Specify dates for viewing.", inline=False)
        await interaction.response.send_message(embed=embed)

    def parse_date(self, date_str):
        if date_str == "today":
            return datetime.now()
        elif date_str == "tomorrow":
            return datetime.now() + timedelta(days=1)
        elif date_str == "yesterday":
            return datetime.now() - timedelta(days=1)
        else:
            return datetime.strptime(date_str, "%d/%m/%Y")

class SleepTrackingModal(discord.ui.Modal, title="Sleep Tracking"):
    hours_slept = discord.ui.TextInput(label="Hours Slept", placeholder="e.g., 7.5")
    score = discord.ui.TextInput(label="Sleep Quality Score (1-5)", placeholder="e.g., 4")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, required=False)
    bed_time = discord.ui.TextInput(label="Bed Time", placeholder="e.g., 22:30")
    wake_time = discord.ui.TextInput(label="Wake Time", placeholder="e.g., 06:30")

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        c.execute('''INSERT INTO sleep_entries 
                     (user_id, hours_slept, score, description, bed_time, wake_time, date) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (interaction.user.id, float(self.hours_slept.value), int(self.score.value),
                   self.description.value, self.bed_time.value, self.wake_time.value, 
                   datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Sleep data recorded successfully!", ephemeral=True)

class DietTrackingModal(discord.ui.Modal, title="Diet Tracking"):
    food = discord.ui.TextInput(label="Food/Ingredient")
    calories = discord.ui.TextInput(label="Calories")
    protein = discord.ui.TextInput(label="Protein (g)")
    fat = discord.ui.TextInput(label="Fat (g)")
    carbs = discord.ui.TextInput(label="Carbs (g)")

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        c.execute('''INSERT INTO diet_entries 
                     (user_id, food, calories, protein, fat, carbs, fiber, date, time) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (interaction.user.id, self.food.value, int(self.calories.value),
                   float(self.protein.value), float(self.fat.value), float(self.carbs.value),
                   0, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Diet data recorded successfully!", ephemeral=True)

class ExerciseTrackingModal(discord.ui.Modal, title="Exercise Tracking"):
    name = discord.ui.TextInput(label="Exercise Name")
    reps = discord.ui.TextInput(label="Number of Reps")
    sets = discord.ui.TextInput(label="Number of Sets")
    variation = discord.ui.TextInput(label="Variation/Weights")
    cool_down = discord.ui.TextInput(label="Cool Down", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        c.execute('''INSERT INTO exercise_entries 
                     (user_id, name, reps, sets, variation, cool_down, date) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (interaction.user.id, self.name.value, int(self.reps.value),
                   int(self.sets.value), self.variation.value, self.cool_down.value,
                   datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Exercise data recorded successfully!", ephemeral=True)

class TodoAddModal(discord.ui.Modal, title="Add Todo"):
    task = discord.ui.TextInput(label="Task")

    def __init__(self, date):
        super().__init__()
        self.date = date

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        target_date = HealthTrackingCog.parse_date(self, self.date).strftime("%Y-%m-%d")
        c.execute('''INSERT INTO todo_entries 
                     (user_id, task, date, completed) 
                     VALUES (?, ?, ?, ?)''',
                  (interaction.user.id, self.task.value, target_date, 0))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Todo added for {target_date}!", ephemeral=True)

class TodoRemoveModal(discord.ui.Modal, title="Remove Todo"):
    task_number = discord.ui.TextInput(label="Task Number to Remove")

    def __init__(self, date):
        super().__init__()
        self.date = date

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        target_date = HealthTrackingCog.parse_date(self, self.date).strftime("%Y-%m-%d")
        c.execute("SELECT id FROM todo_entries WHERE user_id = ? AND date = ? ORDER BY id", 
                  (interaction.user.id, target_date))
        tasks = c.fetchall()
        
        try:
            task_index = int(self.task_number.value) - 1
            if 0 <= task_index < len(tasks):
                task_id = tasks[task_index][0]
                c.execute("DELETE FROM todo_entries WHERE id = ?", (task_id,))
                conn.commit()
                await interaction.response.send_message(f"Todo removed for {target_date}!", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid task number.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
        finally:
            conn.close()

class TodoEditModal(discord.ui.Modal, title="Edit Todo"):
    task_number = discord.ui.TextInput(label="Task Number to Edit")
    new_task = discord.ui.TextInput(label="New Task Description")

    def __init__(self, date):
        super().__init__()
        self.date = date

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        target_date = HealthTrackingCog.parse_date(self, self.date).strftime("%Y-%m-%d")
        c.execute("SELECT id FROM todo_entries WHERE user_id = ? AND date = ? ORDER BY id", 
                  (interaction.user.id, target_date))
        tasks = c.fetchall()
        
        try:
            task_index = int(self.task_number.value) - 1
            if 0 <= task_index < len(tasks):
                task_id = tasks[task_index][0]
                c.execute("UPDATE todo_entries SET task = ? WHERE id = ?", (self.new_task.value, task_id))
                conn.commit()
                await interaction.response.send_message(f"Todo updated for {target_date}!", ephemeral=True)
            else:
                await interaction.response.send_message("Invalid task number.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
        finally:
            conn.close()

class JournalEntryModal(discord.ui.Modal, title="Journal Entry"):
    entry = discord.ui.TextInput(label="Journal Entry", style=discord.TextStyle.long)
    mood = discord.ui.TextInput(label="Mood (1-5)")

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        now = datetime.now()
        c.execute('''INSERT INTO journal_entries 
                     (user_id, entry, date, time, mood) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (interaction.user.id, self.entry.value, now.strftime("%Y-%m-%d"),
                   now.strftime("%H:%M"), int(self.mood.value)))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Journal entry recorded successfully!", ephemeral=True)

class BodyTrackingModal(discord.ui.Modal, title="Body Tracking"):
    mass = discord.ui.TextInput(label="Mass (kg)")
    height = discord.ui.TextInput(label="Height (cm)")
    age = discord.ui.TextInput(label="Age")
    activity_level = discord.ui.TextInput(label="Activity Level (1-5)")
    body_fat = discord.ui.TextInput(label="Body Fat Percentage")

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        now = datetime.now()
        c.execute('''INSERT INTO body_tracking 
                     (user_id, mass_in_kg, height, age, activity_level, body_fat_percentage, time, date) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (interaction.user.id, float(self.mass.value), float(self.height.value),
                   int(self.age.value), int(self.activity_level.value), float(self.body_fat.value),
                   now.strftime("%H:%M"), now.strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Body tracking data recorded successfully!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HealthTrackingCog(bot))
    