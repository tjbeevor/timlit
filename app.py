# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import plotly.graph_objects as go

# Data Classes
@dataclass
class EVPackage:
    model: str
    battery_capacity: float  # kWh
    range: int  # km
    charging_power: float  # kW
    v2g_capable: bool
    base_price: float
    profit_share: float
    features: List[str]

@dataclass
class BatteryPackage:
    capacity: float  # kWh
    peak_power: float  # kW
    cycles: int
    warranty_years: int
    base_price: float
    profit_share: float
    grid_share: float
    features: List[str]

@dataclass
class SolarPackage:
    capacity: float  # kW
    panel_count: int
    panel_power: int  # W
    inverter_size: float  # kW
    base_price: float
    warranty_years: int
    features: List[str]

# AEMO Pricing Class
class AEMOPricing:
    def __init__(self):
        self.price_patterns = {
            'summer_peak': {
                'extreme': {'price': 15.0, 'probability': 0.02},
                'high': {'price': 0.45, 'probability': 0.15},
                'medium': {'price': 0.32, 'probability': 0.33},
                'low': {'price': 0.25, 'probability': 0.50}
            },
            'summer_offpeak': {
                'high': {'price': 0.15, 'probability': 0.10},
                'medium': {'price': 0.08, 'probability': 0.40},
                'low': {'price': 0.03, 'probability': 0.50}
            },
            'winter_peak': {
                'extreme': {'price': 8.0, 'probability': 0.01},
                'high': {'price': 0.38, 'probability': 0.20},
                'medium': {'price': 0.28, 'probability': 0.30},
                'low': {'price': 0.22, 'probability': 0.49}
            },
            'winter_offpeak': {
                'high': {'price': 0.12, 'probability': 0.15},
                'medium': {'price': 0.06, 'probability': 0.35},
                'low': {'price': 0.03, 'probability': 0.50}
            }
        }
        
        self.fcas_revenue = {
            'raise_6s': 0.08,
            'raise_60s': 0.05,
            'raise_5min': 0.03,
            'lower_6s': 0.04,
            'lower_60s': 0.03,
            'lower_5min': 0.02
        }
        
        self.demand_response = {
            'extreme': {'payment': 2.0, 'events_per_year': 5},
            'high': {'payment': 1.0, 'events_per_year': 15},
            'medium': {'payment': 0.5, 'events_per_year': 30}
        }

    def calculate_arbitrage_potential(self, battery_capacity, efficiency=0.9):
        seasons = ['summer_peak', 'summer_offpeak', 'winter_peak', 'winter_offpeak']
        annual_revenue = 0
        
        for season in seasons:
            season_days = 91.25
            daily_revenue = 0
            
            for level, details in self.price_patterns[season].items():
                if 'offpeak' in season and level == 'low':
                    daily_revenue -= battery_capacity * details['price'] * details['probability']
                else:
                    daily_revenue += battery_capacity * details['price'] * details['probability'] * efficiency
            
            annual_revenue += daily_revenue * season_days
        
        return annual_revenue / 12

    def calculate_fcas_revenue(self, battery_capacity, availability=0.95):
        monthly_revenue = 0
        
        for service, rate in self.fcas_revenue.items():
            if '6s' in service:
                participation = 0.10
            elif '60s' in service:
                participation = 0.15
            else:
                participation = 0.25
            
            service_capacity = battery_capacity * participation
            monthly_revenue += service_capacity * rate * 24 * 30 * availability
        
        return monthly_revenue

    def calculate_demand_response_revenue(self, battery_capacity, reliability=0.95):
        annual_revenue = 0
        
        for level, details in self.demand_response.items():
            event_revenue = battery_capacity * details['payment'] * reliability
            annual_revenue += event_revenue * details['events_per_year']
        
        return annual_revenue / 12

# Package definitions
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
        daily_commute = usage_profile.get('daily_commute', 0)
        power_bill = usage_profile.get('power_bill', 0)
        roof_space = usage_profile.get('roof_space', 0)
        
        # Basic recommendation logic
        if daily_commute <= 40:
            ev_rec = 'Essential'
        elif daily_commute <= 80:
            ev_rec = 'Performance'
        else:
            ev_rec = 'Premium'
        
        if power_bill <= 200:
            batt_rec = 'Starter'
        elif power_bill <= 400:
            batt_rec = 'Essential'
        else:
            batt_rec = 'Performance'
        
        if roof_space <= 30:
            solar_rec = 'Starter'
        elif roof_space <= 45:
            solar_rec = 'Essential'
        else:
            solar_rec = 'Performance'
        
        return {
            'ev': ev_rec,
            'battery': batt_rec,
            'solar': solar_rec
        }

class ROICalculator:
    def __init__(self, aemo_pricing):
        self.aemo_pricing = aemo_pricing
        self.interest_rate = 0.049
        self.loan_term_years = 5
        
    def calculate_roi(self, ev, battery, solar, usage_profile):
        # Monthly benefits calculation
        arbitrage_revenue = self.aemo_pricing.calculate_arbitrage_potential(battery.capacity)
        fcas_revenue = self.aemo_pricing.calculate_fcas_revenue(battery.capacity)
        dr_revenue = self.aemo_pricing.calculate_demand_response_revenue(battery.capacity)
        
        # Monthly costs
        total_cost = ev.base_price + battery.base_price + solar.base_price
        monthly_payment = total_cost / (self.loan_term_years * 12)  # Simplified
        
        # Profit sharing
        total_revenue = arbitrage_revenue + fcas_revenue + dr_revenue
        customer_share = total_revenue * (1 - ev.profit_share - battery.profit_share)
        
        # Calculate savings
        current_power_bill = usage_profile.get('power_bill', 0)
        current_fuel_cost = usage_profile.get('fuel_cost', 0)
        
        total_monthly_benefit = (
            customer_share +
            current_power_bill * 0.8 +  # Assume 80% reduction in power bill
            current_fuel_cost * 0.9     # Assume 90% reduction in fuel costs
        )
        
        return {
            'monthly_payment': monthly_payment,
            'monthly_benefit': total_monthly_benefit,
            'net_monthly': total_monthly_benefit - monthly_payment,
            'payback_years': total_cost / (total_monthly_benefit * 12)
        }

def main():
    st.set_page_config(page_title="Energy Package Designer", layout="wide")
    
    st.title("⚡ Energy Independence Package Designer")
    st.subheader("Design your complete energy solution")
    
    # Initialize classes
    aemo = AEMOPricing()
    packages = EnergyPackages()
    roi_calc = ROICalculator(aemo)
    
    # User inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Energy Profile")
        daily_commute = st.slider("Daily Commute (km)", 0, 200, 40)
        power_bill = st.number_input("Monthly Power Bill ($)", 0, 1000, 250)
        fuel_cost = st.number_input("Monthly Fuel Cost ($)", 0, 1000, 200)
        roof_space = st.slider("Available Roof Space (m²)", 0, 100, 40)
        
    usage_profile = {
        'daily_commute': daily_commute,
        'power_bill': power_bill,
        'fuel_cost': fuel_cost,
        'roof_space': roof_space
    }
    
    # Get recommendations
    recommended = packages.get_recommended_package(usage_profile)
    
    with col2:
        st.subheader("Recommended Package")
        st.info(
            f"Based on your profile:\n\n"
            f"🚗 EV: {recommended['ev']}\n"
            f"🔋 Battery: {recommended['battery']}\n"
            f"☀️ Solar: {recommended['solar']}"
        )
    
    # Package selection
    st.header("Package Selection")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_ev = st.selectbox(
            "Choose EV Package",
            options=list(packages.ev_packages.keys()),
            index=list(packages.ev_packages.keys()).index(recommended['ev'])
        )
        ev = packages.ev_packages[selected_ev]
        
        st.write(f"🚗 {ev.model}")
        st.write(f"⚡ {ev.battery_capacity}kWh battery")
        st.write(f"🛣️ {ev.range}km range")
        
    with col2:
        selected_battery = st.selectbox(
            "Choose Battery Package",
            options=list(packages.battery_packages.keys()),
            index=list(packages.battery_packages.keys()).index(recommended['battery'])
        )
        battery = packages.battery_packages[selected_battery]
        
        st.write(f"🔋 {battery.capacity}kWh capacity")
        st.write(f"⚡ {battery.peak_power}kW power")
        st.write(f"✨ {battery.warranty_years} year warranty")
        
    with col3:
        selected_solar = st.selectbox(
            "Choose Solar Package",
            options=list(packages.solar_packages.keys()),
            index=list(packages.solar_packages.keys()).index(recommended['solar'])
        )
        solar = packages.solar_packages[selected_solar]
        
        st.write(f"☀️ {solar.capacity}kW system")
        st.write(f"📊 {solar.panel_count}x {solar.panel_power}W panels")
        st.write(f"✨ {solar.warranty_years} year warranty")
    
    # Calculate ROI
     if st.button("Calculate Financial Benefits", type="primary"):
            roi = roi_calc.calculate_roi(
                packages.ev_packages[selected_ev],
                packages.battery_packages[selected_battery],
                packages.solar_packages[selected_solar],
                usage_profile
            )
        
            st.header("Financial Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Monthly Package Payment",
                    f"${roi['monthly_payment']:.2f}"
                )
            
            with col2:
                st.metric(
                    "Monthly Benefits",
                    f"${roi['monthly_benefit']:.2f}"
                )
                
            with col3:
                st.metric(
                    "Net Monthly Savings",
                    f"${roi['net_monthly']:.2f}",
                    delta=f"${roi['net_monthly'] - power_bill:.2f} vs current"
                )
                
            with col4:
                st.metric(
                    "Payback Period",
                    f"{roi['payback_years']:.1f} years"
                )
        
        # Detailed breakdown
        st.subheader("Monthly Breakdown")
        fig = go.Figure()
        
        # Revenue chart
        revenues = {
            'Energy Trading': roi['monthly_benefit'] * 0.3,
            'Power Bill Savings': power_bill * 0.8,
            'Fuel Savings': fuel_cost * 0.9
        }
        
        colors = ['#2ecc71', '#3498db', '#e74c3c']
        
        fig.add_trace(go.Bar(
            name='Monthly Benefits',
            x=list(revenues.keys()),
            y=list(revenues.values()),
            marker_color=colors
        ))
        
        fig.update_layout(
            title='Monthly Benefit Breakdown',
            yaxis_title='Amount ($)',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Grid services
        st.subheader("Grid Services Revenue")
        col1, col2 = st.columns(2)
        
        with col1:
            fcas_rev = aemo.calculate_fcas_revenue(battery.capacity)
            st.metric(
                "Monthly FCAS Revenue",
                f"${fcas_rev:.2f}",
                help="Revenue from frequency control ancillary services"
            )
            
        with col2:
            dr_rev = aemo.calculate_demand_response_revenue(battery.capacity)
            st.metric(
                "Monthly Demand Response",
                f"${dr_rev:.2f}",
                help="Revenue from demand response events"
            )
        
        # AEMO price patterns
        st.subheader("Energy Market Prices")
        price_fig = go.Figure()
        
        for season in ['summer_peak', 'winter_peak']:
            prices = []
            probabilities = []
            for level, details in aemo.price_patterns[season].items():
                prices.append(details['price'])
                probabilities.append(details['probability'])
            
            price_fig.add_trace(go.Scatter(
                x=prices,
                y=probabilities,
                name=season.replace('_', ' ').title(),
                mode='lines+markers'
            ))
        
        price_fig.update_layout(
            title='Price Distribution by Season',
            xaxis_title='Price ($/kWh)',
            yaxis_title='Probability',
            height=400
        )
        
        st.plotly_chart(price_fig, use_container_width=True)
        
        # Package features
        st.subheader("Package Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("🚗 EV Features")
            for feature in ev.features:
                st.write(f"✓ {feature}")
                
        with col2:
            st.write("🔋 Battery Features")
            for feature in battery.features:
                st.write(f"✓ {feature}")
                
        with col3:
            st.write("☀️ Solar Features")
            for feature in solar.features:
                st.write(f"✓ {feature}")
        
        # Disclaimer
        st.markdown("---")
        st.caption(
            "Note: All calculations are estimates based on current market rates and "
            "typical usage patterns. Actual results may vary. FCAS and demand response "
            "revenues are subject to market conditions and availability."
        )

if __name__ == "__main__":
    main()
