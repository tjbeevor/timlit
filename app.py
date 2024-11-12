import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="⚡ Energy Independence Package Designer ⚡", layout="wide", page_icon="🌞")

# Custom CSS to adjust the look and feel
st.markdown("""
    <style>
    body {
        background-color: #1F1B24;
        color: #E0E0E0;
    }
    h1, h2, h3 {
        color: #00FFB3 !important; /* Fluoro Green */
        font-weight: bold;
    }
    h1 {
        text-shadow: 2px 2px #FF6BD6; /* Fluorescent Pink Shadow */
    }
    .stButton>button {
        background-color: #FF8C00 !important; /* Bright Orange */
        color: #FFFFFF;
        border-radius: 12px;
        height: 3em;
        width: 100%;
        font-size: 1.3em;
        box-shadow: 0 4px 15px rgba(255, 0, 150, 0.4); /* Pink Glow */
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
    }
    .stMetric {
        font-size: 1.5em;
        color: #00EFFF; /* Neon Blue */
    }
    .stInfo {
        background-color: #FF6BD6;
        border-radius: 8px;
        padding: 10px;
        color: #1F1B24;
        font-weight: bold;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Data Classes
@dataclass
class EVPackage:
    model: str
    battery_capacity: float
    range: int
    charging_power: float
    v2g_capable: bool
    base_price: float
    profit_share: float
    features: List[str]

@dataclass
class BatteryPackage:
    capacity: float
    peak_power: float
    cycles: int
    warranty_years: int
    base_price: float
    profit_share: float
    grid_share: float
    features: List[str]

@dataclass
class SolarPackage:
    capacity: float
    panel_count: int
    panel_power: int
    inverter_size: float
    base_price: float
    warranty_years: int
    features: List[str]

class EnergyPackages:
    def __init__(self):
        self.ev_packages = {
            'Essential': EVPackage(
                model="BYD Atto 3",
                battery_capacity=60.0,
                range=400,
                charging_power=7.0,
                v2g_capable=True,
                base_price=650,
                profit_share=0.15,
                features=['Vehicle-to-grid ready', 'Smart charging', '7kW AC charging']
            ),
            'Performance': EVPackage(
                model="Tesla Model 3",
                battery_capacity=75.0,
                range=510,
                charging_power=11.0,
                v2g_capable=True,
                base_price=850,
                profit_share=0.12,
                features=['Premium interior', '11kW AC charging', 'Advanced autopilot']
            ),
            'Premium': EVPackage(
                model="Tesla Model Y",
                battery_capacity=82.0,
                range=530,
                charging_power=11.0,
                v2g_capable=True,
                base_price=950,
                profit_share=0.12,
                features=['SUV format', 'Premium interior', '11kW AC charging']
            )
        }
        
        self.battery_packages = {
            'Starter': BatteryPackage(
                capacity=10.0,
                peak_power=5.0,
                cycles=6000,
                warranty_years=10,
                base_price=150,
                profit_share=0.20,
                grid_share=0.30,
                features=['Basic backup power', 'Solar integration', 'Smart monitoring']
            ),
            'Essential': BatteryPackage(
                capacity=15.0,
                peak_power=7.5,
                cycles=6000,
                warranty_years=10,
                base_price=200,
                profit_share=0.18,
                grid_share=0.30,
                features=['Extended backup power', 'Solar integration', 'Smart monitoring']
            ),
            'Performance': BatteryPackage(
                capacity=20.0,
                peak_power=10.0,
                cycles=8000,
                warranty_years=12,
                base_price=250,
                profit_share=0.15,
                grid_share=0.30,
                features=['Whole home backup', 'Advanced monitoring', 'FCAS participation']
            )
        }

        self.solar_packages = {
            'Starter': SolarPackage(
                capacity=6.6,
                panel_count=12,
                panel_power=550,
                inverter_size=5.0,
                base_price=100,
                warranty_years=10,
                features=['Basic monitoring', 'Single phase']
            ),
            'Essential': SolarPackage(
                capacity=8.8,
                panel_count=16,
                panel_power=550,
                inverter_size=8.0,
                base_price=130,
                warranty_years=12,
                features=['Advanced monitoring', 'Single phase', 'Panel optimization']
            ),
            'Performance': SolarPackage(
                capacity=13.2,
                panel_count=24,
                panel_power=550,
                inverter_size=10.0,
                base_price=180,
                warranty_years=12,
                features=['Premium panels', 'Three phase', 'Panel optimization']
            )
        }

    def get_recommended_package(self, usage_profile):
        """Generate package recommendations based on user input"""
        daily_commute = usage_profile['daily_commute']
        power_bill = usage_profile['power_bill']
        roof_space = usage_profile['roof_space']

        ev = 'Essential' if daily_commute < 50 else 'Performance' if daily_commute < 100 else 'Premium'
        battery = 'Starter' if power_bill < 200 else 'Essential' if power_bill < 400 else 'Performance'
        solar = 'Starter' if roof_space < 30 else 'Essential' if roof_space < 50 else 'Performance'

        return {'ev': ev, 'battery': battery, 'solar': solar}

# Initialize package selection
packages = EnergyPackages()

st.markdown("<h1>⚡ Energy Package Designer ⚡</h1>", unsafe_allow_html=True)

# User inputs
col1, col2 = st.columns(2)
with col1:
    st.markdown("<h2>Your Energy Profile</h2>", unsafe_allow_html=True)
    daily_commute = st.slider("Daily Commute (km)", 0, 200, 40)
    power_bill = st.number_input("Monthly Power Bill ($)", 0, 1000, 250)
    roof_space = st.slider("Available Roof Space (m²)", 0, 100, 40)

usage_profile = {
    'daily_commute': daily_commute,
    'power_bill': power_bill,
    'roof_space': roof_space
}

# Get recommendations
recommended = packages.get_recommended_package(usage_profile)
with col2:
    st.markdown("<h2>Recommended Package</h2>", unsafe_allow_html=True)
    st.info(
        f"🚗 **EV**: {recommended['ev']} \n"
        f"🔋 **Battery**: {recommended['battery']} \n"
        f"☀️ **Solar**: {recommended['solar']}"
    )

# Display package details
st.markdown("<h2>Package Details</h2>", unsafe_allow_html=True)
st.write("Choose from the recommended packages to view more details and calculate ROI.")

if st.button("Get Started!"):
    st.balloons()
