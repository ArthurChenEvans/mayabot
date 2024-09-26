import discord
from discord import app_commands
from discord.ext import commands

class StudyHelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="study_help", description="Get study tips and techniques")
    @app_commands.choices(topic=[
        app_commands.Choice(name="Flashcards", value="flashcards"),
        app_commands.Choice(name="Anki", value="anki")
    ])
    async def study_help(self, interaction: discord.Interaction, topic: app_commands.Choice[str]):
        if topic.value == "flashcards":
            await interaction.response.send_message(self.get_flashcard_tips())
        elif topic.value == "anki":
            await interaction.response.send_message(self.get_anki_tips())

    def get_flashcard_tips(self):
        return """
# Why Spacing and Repetition Improve Memory

1. Spaced repetition leverages the spacing effect - memories decay over time, but reviewing information at gradually increasing intervals can halt this decay and strengthen long-term retention.
2. Retrieval practice (actively recalling information) is more effective for learning than passive review. Spaced repetition provides opportunities for repeated retrieval attempts.
3. Effortful retrieval strengthens memory more than easy retrieval. Spacing out reviews makes retrieval more challenging but beneficial.

# How Anki Improves Memory

1. Anki automates the spacing of reviews, showing cards less frequently as they are successfully recalled.
2. It allows for personalized scheduling based on individual performance on each card.
3. The digital format makes it easy to create, edit, and review large numbers of flashcards.
4. Anki can be used on multiple devices, enabling convenient review.

# Leveraging the 3 Elements of Effective Learning and 5 Principles for Good Flashcards

## Three Elements of Effective Learning

1. Cue availability - having retrieval cues that allow expression of knowledge
2. Cue diagnosticity - cues that uniquely specify target knowledge
3. Elaboration - adding detail to make knowledge distinctive and organized

## Five Principles for Good Flashcards

1. Make cards focused on one idea
2. Use precise language
3. Ensure cards produce consistent answers
4. Make cards tractable (almost always answerable)
5. Require effortful recall

# Examples of Applying These Principles

1. Break complex topics into multiple focused cards:
   Instead of: "Describe the process of photosynthesis"
   Better: "What are the two main stages of photosynthesis?"
           "In which stage of photosynthesis is oxygen produced?"

2. Use precise language:
   Instead of: "What happens in photosynthesis?"
   Better: "What is the primary energy input for photosynthesis?"

3. Ensure consistent answers:
   Instead of: "List some products of photosynthesis"
   Better: "What are the three main products of photosynthesis?"

4. Make cards tractable:
   Instead of: "Explain the Calvin cycle"
   Better: "What is the main purpose of the Calvin cycle in photosynthesis?"

5. Require effortful recall:
   Instead of: "Photosynthesis uses sunlight, water and ___ to produce energy"
   Better: "What three inputs are required for photosynthesis?"

If you want to know more or have further questions ping @nekosagichen_63550
"""

    def get_anki_tips(self):
        return """
# How to Use Anki Effectively

Anki is a powerful spaced repetition software that can significantly improve your learning and retention. Here are some tips to make the most of Anki:

## Creating Effective Anki Cards

1. Focus on one concept per card:
   Instead of: "List all the bones in the human hand"
   Better: "What are the five metacarpal bones in the human hand?"

2. Use precise language:
   Instead of: "What does DNA do?"
   Better: "What is the primary function of DNA in a cell?"

3. Ensure consistent answers:
   Instead of: "Name some types of chemical bonds"
   Better: "What are the three main types of chemical bonds?"

4. Make cards answerable:
   Instead of: "Explain quantum mechanics"
   Better: "What is the key principle of quantum superposition?"

5. Require active recall:
   Instead of: "The capital of France is P____"
   Better: "What is the capital of France?"

## Additional Anki Tips

1. Use cloze deletions for lists or processes:
   "The steps of mitosis are: {{c1::prophase}}, {{c2::metaphase}}, {{c3::anaphase}}, {{c4::telophase}}."

2. Include explanations to reinforce understanding:
   Q: "What is the function of mitochondria in a cell?"
   A: "Produce energy (ATP) through cellular respiration. They are often called the 'powerhouse' of the cell."

3. Create bidirectional cards:
   Card 1: Q: "What is the chemical symbol for gold?"
           A: "Au"
   Card 2: Q: "What element has the chemical symbol Au?"
           A: "Gold"

4. Use images where appropriate:
   Q: "Identify the parts of a neuron in this image: [neuron diagram]"
   A: "[labeled neuron diagram]"

5. Regularly review and refine your cards:
   - Delete cards you no longer need
   - Split complex cards into simpler ones
   - Improve unclear or ambiguous cards

Remember, the key to success with Anki is consistent daily review and creating high-quality cards that promote active recall and understanding.

If you want to know more or have further questions ping @nekosagichen_63550
"""

async def setup(bot):
    await bot.add_cog(StudyHelpCog(bot))