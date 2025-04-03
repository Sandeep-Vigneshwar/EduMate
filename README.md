# EduMate

EduMate is an intelligent platform for extracting, organizing, and mapping educational content. It processes Course Development Plans (CDPs), maps course outcomes (COs) to portions, categorizes professor-provided materials, and scrapes relevant online resources.

## 💡 Key Highlights

- 📜 **CDP Extraction**: Extracts course outcomes and portions from Course Development Plans.
- 📌 **Content Mapping**: Maps extracted data to relevant portions and course outcomes.
- 📂 **Material Categorization**: Organizes professor-provided materials under COs and portions.
- 🌐 **Web Scraping**: Fetches online resources to enhance learning materials.

## 📁 Project Structure

```
EduMate/
│── src/
│   ├── extraction.py    # Extracts COs and portions from CDPs
│   ├── scraping.py      # Scrapes online resources based on COs and portions
│   ├── db_handler.py    # Handles database operations for structured storage
│   ├── cleaning.py      # Cleans and preprocesses extracted data
│   ├── main.py          # Main entry point of the application
│── requirements.txt     # List of required dependencies
│── README.md            # Project documentation
```

## 🛠 Installation & Usage

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/EduMate.git
   cd EduMate
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run the main script:**
   ```sh
   python src/main.py
   ```

## 🚀 Future Enhancements

- 🤖 **AI-based Content Recommendation**: Suggests relevant educational materials based on user interaction.
- 📊 **Data Visualization**: Generates insights and statistics about course content.
- 🔍 **Improved Web Scraping**: More robust methods for fetching high-quality educational resources.

## 👨‍💻 Contributors
- **Dharmadhaashan P** - GitHub: [https://github.com/Dharmadhaashan](Link)
- **Sanjay S** - GitHub: [https://github.com/sanjayssrini](Link)

Everyone are welcomed to punch your creativity by contributing in our project!
