"""
Synthetic Data Generator for CPM Enterprise Blueprint
======================================================

Generates realistic public media constituent data for testing and demos.

Datasets Generated:
- WBEZ donations (one-time and recurring)
- Sun-Times subscriptions  
- Event tickets
- Email engagement
- Ground truth mapping

Author: Catherine Kiriakos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple
from pathlib import Path
import json


@dataclass
class GeneratorConfig:
    """Configuration for synthetic data generation."""
    num_constituents: int = 5000
    overlap_rate: float = 0.25
    date_start: str = "2020-01-01"
    date_end: str = "2025-12-31"
    sustainer_rate: float = 0.35
    churn_rate: float = 0.15
    seed: int = 42


class SyntheticDataGenerator:
    """Generates realistic synthetic data for public media constituents."""
    
    # Chicago-area realistic data
    FIRST_NAMES = [
        "James", "Mary", "Michael", "Patricia", "Robert", "Jennifer", "David", "Linda",
        "William", "Elizabeth", "Richard", "Barbara", "Joseph", "Susan", "Thomas", "Jessica",
        "Christopher", "Sarah", "Charles", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
        "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
        "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle",
        "Kevin", "Dorothy", "Brian", "Carol", "George", "Amanda", "Timothy", "Melissa"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
    ]
    
    CHICAGO_STREETS = [
        "Michigan Ave", "State St", "Clark St", "Dearborn St", "LaSalle St",
        "Wells St", "Franklin St", "Wacker Dr", "Madison St", "Monroe St",
        "Adams St", "Jackson Blvd", "Van Buren St", "Congress Pkwy", "Harrison St",
        "Roosevelt Rd", "Cermak Rd", "Archer Ave", "Ashland Ave", "Western Ave",
        "California Ave", "Kedzie Ave", "Pulaski Rd", "Cicero Ave", "Central Ave",
        "Oak Park Ave", "Harlem Ave", "Irving Park Rd", "Belmont Ave", "Fullerton Ave",
        "Diversey Pkwy", "Armitage Ave"
    ]
    
    CHICAGO_NEIGHBORHOODS = {
        "Loop": "60601", "River North": "60654", "Gold Coast": "60610",
        "Lincoln Park": "60614", "Lakeview": "60657", "Wicker Park": "60622",
        "Logan Square": "60647", "Hyde Park": "60615", "Oak Park": "60302",
        "Evanston": "60201"
    }
    
    EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", 
                    "icloud.com", "aol.com", "comcast.net", "att.net",
                    "sbcglobal.net", "msn.com"]
    
    CAMPAIGNS = ["SPRING24", "FALL23", "EOY23", "MATCH24", "JOURNALISM", 
                 "SUSTAINER", "ONLINE", "RADIO", "PODCAST"]
    
    def __init__(self, config: GeneratorConfig = None):
        self.config = config or GeneratorConfig()
        np.random.seed(self.config.seed)
        self._people = []
        
    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """Generate all datasets."""
        # Generate base population
        self._generate_people()
        
        datasets = {
            'ground_truth': self._create_ground_truth(),
            'wbez_donations': self._generate_wbez_donations(),
            'suntimes_subscriptions': self._generate_suntimes_subscriptions(),
            'event_tickets': self._generate_event_tickets(),
            'email_engagement': self._generate_email_engagement(),
        }
        
        return datasets
    
    def _generate_people(self):
        """Generate base population of people."""
        for i in range(self.config.num_constituents):
            first_name = np.random.choice(self.FIRST_NAMES)
            last_name = np.random.choice(self.LAST_NAMES)
            neighborhood = np.random.choice(list(self.CHICAGO_NEIGHBORHOODS.keys()))
            
            person = {
                'person_id': f'P-{i:08d}',
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{first_name.lower()}.{last_name.lower()}{np.random.randint(1, 99)}@{np.random.choice(self.EMAIL_DOMAINS)}",
                'phone': f"{np.random.choice(['312', '773', '872', '630', '847'])}{np.random.randint(1000000, 9999999)}",
                'address': f"{np.random.randint(100, 9999)} {np.random.choice(self.CHICAGO_STREETS)}",
                'city': neighborhood if neighborhood in ['Oak Park', 'Evanston'] else 'Chicago',
                'state': 'IL',
                'zip': self.CHICAGO_NEIGHBORHOODS[neighborhood],
                'engagement_level': np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.4, 0.2]),
                'giving_capacity': np.random.choice(['low', 'medium', 'high', 'major'], p=[0.5, 0.3, 0.15, 0.05]),
            }
            self._people.append(person)
    
    def _create_ground_truth(self) -> pd.DataFrame:
        """Create ground truth mapping of person to source systems."""
        return pd.DataFrame(self._people)
    
    def _generate_wbez_donations(self) -> pd.DataFrame:
        """Generate WBEZ donation records."""
        donations = []
        
        for person in self._people:
            # Determine if sustainer
            is_sustainer = np.random.random() < self.config.sustainer_rate
            
            # Determine giving based on capacity
            capacity_amounts = {
                'low': (10, 100),
                'medium': (25, 250),
                'high': (50, 500),
                'major': (250, 5000)
            }
            min_amt, max_amt = capacity_amounts[person['giving_capacity']]
            
            if is_sustainer:
                # Generate recurring donations
                start_date = pd.Timestamp(self.config.date_start) + timedelta(
                    days=np.random.randint(0, 365)
                )
                monthly_amount = max(10, np.random.randint(10, max(15, max_amt // 10)))
                
                # Determine if churned
                churned = np.random.random() < self.config.churn_rate
                if churned:
                    num_months = np.random.randint(3, 24)
                else:
                    num_months = min(60, int((datetime.now() - start_date).days / 30))
                
                for month in range(num_months):
                    donation_date = start_date + timedelta(days=month * 30)
                    if donation_date > datetime.now():
                        break
                    
                    donations.append({
                        'donation_id': f"D-{len(donations):08d}",
                        'person_id': person['person_id'],
                        'email': person['email'],
                        'first_name': person['first_name'],
                        'last_name': person['last_name'],
                        'phone': person['phone'],
                        'address': person['address'],
                        'city': person['city'],
                        'state': person['state'],
                        'zip': person['zip'],
                        'donation_date': donation_date.strftime('%Y-%m-%d'),
                        'amount': monthly_amount,
                        'donation_type': 'recurring',
                        'campaign': 'SUSTAINER',
                        'payment_method': np.random.choice(['credit_card', 'ach']),
                    })
            else:
                # Generate one-time donations
                num_donations = np.random.choice([0, 1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.07, 0.03])
                
                for _ in range(num_donations):
                    donation_date = pd.Timestamp(self.config.date_start) + timedelta(
                        days=np.random.randint(0, 1800)
                    )
                    
                    donations.append({
                        'donation_id': f"D-{len(donations):08d}",
                        'person_id': person['person_id'],
                        'email': person['email'],
                        'first_name': person['first_name'],
                        'last_name': person['last_name'],
                        'phone': person['phone'],
                        'address': person['address'],
                        'city': person['city'],
                        'state': person['state'],
                        'zip': person['zip'],
                        'donation_date': donation_date.strftime('%Y-%m-%d'),
                        'amount': np.random.randint(min_amt, max_amt),
                        'donation_type': 'one_time',
                        'campaign': np.random.choice(self.CAMPAIGNS),
                        'payment_method': np.random.choice(['credit_card', 'paypal', 'check']),
                    })
        
        return pd.DataFrame(donations)
    
    def _generate_suntimes_subscriptions(self) -> pd.DataFrame:
        """Generate Sun-Times subscription records."""
        subscriptions = []
        
        # Only some people have subscriptions
        sub_rate = 0.15
        
        for person in self._people:
            if np.random.random() > sub_rate:
                continue
            
            sub_type = np.random.choice(['DIGITAL', 'WEEKEND', 'DAILY', 'PREMIUM'],
                                        p=[0.5, 0.25, 0.15, 0.1])
            rates = {'DIGITAL': 9.99, 'WEEKEND': 14.99, 'DAILY': 24.99, 'PREMIUM': 34.99}
            
            start_date = pd.Timestamp(self.config.date_start) + timedelta(
                days=np.random.randint(0, 1500)
            )
            
            # Use slightly different email sometimes
            email = person['email']
            if np.random.random() < 0.3:
                email = f"{person['first_name'][0].lower()}{person['last_name'].lower()}@{np.random.choice(self.EMAIL_DOMAINS)}"
            
            subscriptions.append({
                'subscription_id': f"S-{len(subscriptions):08d}",
                'person_id': person['person_id'],
                'email': email,
                'first_name': person['first_name'],
                'last_name': person['last_name'],
                'phone': person['phone'],
                'address': person['address'],
                'city': person['city'],
                'state': person['state'],
                'zip': person['zip'],
                'subscription_type': sub_type,
                'monthly_rate': rates[sub_type],
                'start_date': start_date.strftime('%Y-%m-%d'),
                'status': np.random.choice(['active', 'cancelled'], p=[0.75, 0.25]),
            })
        
        return pd.DataFrame(subscriptions)
    
    def _generate_event_tickets(self) -> pd.DataFrame:
        """Generate event ticket records."""
        tickets = []
        
        events = [
            ("Wait Wait Live", 75), ("StoryCorps Recording", 0), ("News Night", 50),
            ("Podcast Festival", 35), ("Annual Gala", 250), ("Election Watch", 25),
        ]
        
        for person in self._people:
            if person['engagement_level'] == 'low':
                num_events = np.random.choice([0, 1], p=[0.8, 0.2])
            elif person['engagement_level'] == 'medium':
                num_events = np.random.choice([0, 1, 2], p=[0.5, 0.35, 0.15])
            else:
                num_events = np.random.choice([1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.1])
            
            for _ in range(num_events):
                event_name, price = events[np.random.randint(0, len(events))]
                event_date = pd.Timestamp(self.config.date_start) + timedelta(
                    days=np.random.randint(0, 1800)
                )
                
                tickets.append({
                    'ticket_id': f"T-{len(tickets):08d}",
                    'person_id': person['person_id'],
                    'email': person['email'],
                    'first_name': person['first_name'],
                    'last_name': person['last_name'],
                    'event_name': event_name,
                    'event_date': event_date.strftime('%Y-%m-%d'),
                    'ticket_price': price,
                    'quantity': np.random.choice([1, 2], p=[0.6, 0.4]),
                })
        
        return pd.DataFrame(tickets)
    
    def _generate_email_engagement(self) -> pd.DataFrame:
        """Generate email engagement records."""
        engagements = []
        
        for person in self._people:
            # Emails received
            num_emails = np.random.randint(30, 80)
            
            open_rate = {'low': 0.15, 'medium': 0.35, 'high': 0.55}[person['engagement_level']]
            
            for i in range(num_emails):
                send_date = pd.Timestamp(self.config.date_start) + timedelta(
                    days=np.random.randint(0, 1800)
                )
                opened = np.random.random() < open_rate
                clicked = opened and np.random.random() < 0.25
                
                engagements.append({
                    'engagement_id': f"E-{len(engagements):08d}",
                    'person_id': person['person_id'],
                    'email': person['email'],
                    'send_date': send_date.strftime('%Y-%m-%d'),
                    'email_type': np.random.choice(['newsletter', 'appeal', 'event', 'update']),
                    'opened': opened,
                    'clicked': clicked,
                })
        
        return pd.DataFrame(engagements)
    
    def save_datasets(self, output_dir: str = "data/synthetic"):
        """Generate and save all datasets to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        datasets = self.generate_all()
        
        for name, df in datasets.items():
            csv_path = output_path / f"{name}.csv"
            json_path = output_path / f"{name}.json"
            
            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient='records', indent=2)
            
            print(f"Saved {name}: {len(df):,} records")
        
        print(f"\nDatasets saved to: {output_path}")


if __name__ == "__main__":
    config = GeneratorConfig(
        num_constituents=5000,
        overlap_rate=0.25,
        sustainer_rate=0.35,
        churn_rate=0.15,
    )
    
    generator = SyntheticDataGenerator(config)
    generator.save_datasets()