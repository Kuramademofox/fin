import os
import openai
from dotenv import load_dotenv
import pandas as pd
import PyPDF2
import io
import json
from datetime import datetime, timedelta
import sqlite3

# Load environment variables
print("Loading environment variables...")
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("OpenAI API key not found. Please set it in your environment variables.")
    exit(1)

# Set OpenAI API key
openai.api_key = "sk-svcacct-MtADhxCOjkp0MT8_LbY3FASyWLO_eGO1fIcxlYyt0xZLj01V8jck1ivTga-xeT3BlbkFJFtlPx_wwNJklWr_nhGjfRNr_5-MrQjajo3z8DJu9iTmFlDp6-TATdXH-oWRtgA"

# Initialize SQLite database
conn = sqlite3.connect('bookkeeping.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (date TEXT, description TEXT, amount REAL)''')
conn.commit()

def get_openai_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error in OpenAI API call: {e}"

# Extract financial data from PDFs
def process_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        return f"Error processing PDF: {e}"

# Add transaction to the database
def add_transaction(date, description, amount):
    c.execute("INSERT INTO transactions VALUES (?, ?, ?)", (date, description, amount))
    conn.commit()

# Get transactions based on the period (daily, weekly, monthly)
def get_transactions(period):
    today = datetime.now().date()
    if period == 'daily':
        c.execute("SELECT * FROM transactions WHERE date = ?", (today,))
    elif period == 'weekly':
        week_start = today - timedelta(days=today.weekday())  # Start of the week (Sunday)
        c.execute("SELECT * FROM transactions WHERE date >= ?", (week_start,))
    elif period == 'monthly':
        month_start = today.replace(day=1)  # First day of the month
        c.execute("SELECT * FROM transactions WHERE date >= ?", (month_start,))
    else:
        return "Invalid period specified"
    return c.fetchall()

# Calculate profit/loss
def calculate_profit_loss(period):
    transactions = get_transactions(period)
    return sum(transaction[2] for transaction in transactions)  # Sum of amounts

# Generate financial reports
def generate_report(period):
    transactions = get_transactions(period)
    profit_loss = calculate_profit_loss(period)
    report = f"{period.capitalize()} Report:\n"
    for transaction in transactions:
        report += f"Date: {transaction[0]}, Description: {transaction[1]}, Amount: {transaction[2]}\n"
    report += f"Total Profit/Loss: {profit_loss}\n"
    
    # Predict future profit/loss based on trends
    future_analysis = predict_future_profit_loss(transactions)
    report += f"\nPrediction: {future_analysis}\n"
    return report

# Predict future profit/loss
def predict_future_profit_loss(transactions):
    if len(transactions) > 0:
        prompt = f"Given the following transaction data: {transactions}, predict the future profit or loss."
        return get_openai_response(prompt)
    else:
        return "Not enough data to predict future profit/loss."

def main():
    while True:
        command = input("Enter a command (or 'quit' to exit): ").lower()
        
        if command == 'quit':
            break
        
        elif command.startswith('add transaction'):
            date = input("Enter date (YYYY-MM-DD): ")
            description = input("Enter description: ")
            amount = float(input("Enter amount: "))
            add_transaction(date, description, amount)
            print("Transaction added successfully.")
        
        elif command.startswith('process pdf'):
            file_path = input("Enter PDF file path: ")
            pdf_content = process_pdf(file_path)
            print("PDF Content:")
            print(pdf_content[:500] + "..." if len(pdf_content) > 500 else pdf_content)
            analysis = get_openai_response(f"Analyze this financial document and provide a summary: {pdf_content[:1000]}")
            print("AI Analysis:")
            print(analysis)
        
        elif command.startswith('get report'):
            period = input("Enter period (daily/weekly/monthly): ")
            report = generate_report(period)
            print(report)
        
        elif command.startswith('analyze'):
            query = command[8:]  # Remove 'analyze ' from the beginning
            response = get_openai_response(f"Analyze this financial query and provide insights: {query}")
            print("AI Analysis:")
            print(response)
        
        else:
            print("Unknown command. Available commands: add transaction, process pdf, get report, analyze")

if __name__ == "__main__":
    print("Welcome to the AI-Powered Automated Financial System")
    main()
    conn.close()
