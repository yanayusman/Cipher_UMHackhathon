# MEX Assistant - AI Business Assistant

MEX Assistant is an intelligent chat-based AI assistant designed to help Grab merchant-partners (MEX) make better business decisions through real-time insights and personalized guidance.

## Presentation Slides, Demo Video and Documentation can be found here:
```
https://drive.google.com/drive/folders/1DSLjceEUFvc8DS12Rmz7tmuSBVfDzGII?usp=drive_link 
```

## Features

- **Real-time Business Insights**
  - Daily sales summaries with growth metrics
  - Top-selling items analysis
  - Inventory monitoring and alerts
  - Sales trends and patterns
  - Customer behavior analysis
  - Profitability insights
  - Seasonal trend analysis

- **Personalized Merchant Guidance**
  - Business type-specific recommendations
  - Size-appropriate suggestions
  - Location-based insights
  - Competitive analysis
  - Data-driven business tips
  - Promotion effectiveness analysis

- **Multilingual Support**
  - English
  - Bahasa Melayu
  - 中文 (Chinese)
  - Tiếng Việt (Vietnamese)
  - ภาษาไทย (Thai)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd MEX-Assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run chat_interface.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Login with your merchant credentials:
   - Select your merchant name from the dropdown
   - Enter the password (default: 1234)

4. Configure your preferences in the sidebar:
   - Select your preferred language
   - Choose your business type
   - Specify your business size

5. Start chatting with the assistant about:
   - Sales and revenue
   - Inventory levels
   - Business tips and suggestions
   - Market trends
   - Customer behavior
   - Promotions and marketing
   - Seasonal patterns

## Project Structure

```
MEX-Assistant/
├── app.py                 # Main Streamlit application
├── chat_interface.py      # Enhanced chat interface
├── logic.py              # Business logic and analytics
├── helper.py             # Helper functions and analytics
├── data_loader.py        # Data loading utilities
├── requirements.txt      # Project dependencies
├── .streamlit/           # Streamlit configuration
├── transaction_data.csv  # Sales transaction records
├── transaction_items.csv # Individual item details
├── items.csv            # Product catalog
├── merchant.csv         # Merchant information
└── keywords.csv         # Multilingual keywords
```

## Dependencies

- streamlit==1.31.1
- pandas==2.2.0
- numpy==1.26.3
- python-dotenv==1.0.1
- plotly==5.18.0
- openai==1.12.0
- langchain==0.1.4

## Data Sources

The assistant uses the following data files:
- `transaction_data.csv`: Sales transaction records
- `transaction_items.csv`: Individual item details per transaction
- `items.csv`: Product catalog
- `merchant.csv`: Merchant information
- `keywords.csv`: Multilingual keywords and phrases

## Features in Detail

### Sales Analysis
- Daily, weekly, and monthly sales summaries
- Growth rate calculations
- Best and worst performing days
- Peak hours analysis
- Average order value tracking

### Inventory Management
- Low stock alerts
- Sales frequency analysis
- Stockout predictions
- Inventory optimization suggestions
- Reorder recommendations

### Business Insights
- Personalized business tips
- Promotion effectiveness analysis
- Customer behavior patterns
- Seasonal trend analysis
- Profitability metrics

### Customer Analytics
- Peak hours identification
- Popular cuisines analysis
- Order patterns
- Customer preferences
- Sales patterns by time of day

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Grab for providing the opportunity to develop this solution
- The development team for their contributions
- All merchant-partners for their valuable feedback
- The open-source community for their tools and libraries
