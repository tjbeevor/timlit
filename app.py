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
        self.interest_rate = 0.049  # 4.9% p.a.
        self.loan_term_years = 5
        
        self.maintenance_costs = {
            'ev': {
                'annual_service': 300,      # Annual service cost
                'tires': 1000,             # Every 40,000 km
                'battery_degradation': 0.02 # 2% capacity loss per year
            },
            'solar': {
                'cleaning': 200,            # Annual cleaning
                'inverter_replacement': 2000, # Every 10 years
                'degradation': 0.007        # 0.7% annual output degradation
            },
            'battery': {
                'annual_check': 150,        # Annual health check
                'degradation': 0.03,        # 3% capacity loss per year
                'replacement': 10           # Expected life in years
            }
        }

    def calculate_monthly_payment(self, principal, years=5, rate=0.049):
        """Calculate monthly loan payment"""
        monthly_rate = rate / 12
        months = years * 12
        return principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)

    def calculate_detailed_roi(self, ev, battery, solar, usage_profile, years=10):
        """Calculate detailed ROI with monthly breakdown over specified years"""
        months = years * 12
        monthly_data = []
        
        # Initial costs
        system_costs = {
            'ev': ev.base_price,
            'battery': battery.base_price,
            'solar': solar.base_price,
            'installation': (battery.base_price + solar.base_price) * 0.15  # 15% installation cost
        }
        
        total_principal = sum(system_costs.values())
        monthly_payment = self.calculate_monthly_payment(total_principal)
        
        # Monthly calculations
        for month in range(months):
            year = month / 12
            
            # Calculate degradation factors
            battery_capacity_factor = (1 - self.maintenance_costs['battery']['degradation']) ** year
            solar_output_factor = (1 - self.maintenance_costs['solar']['degradation']) ** year
            
            # Calculate maintenance costs
            maintenance = {
                'ev_maintenance': (self.maintenance_costs['ev']['annual_service'] / 12 +
                                 (self.maintenance_costs['ev']['tires'] / 48)),  # Assuming tires every 4 years
                'solar_maintenance': (self.maintenance_costs['solar']['cleaning'] / 12 +
                                    self.maintenance_costs['solar']['inverter_replacement'] / (120)),  # 10 years
                'battery_maintenance': self.maintenance_costs['battery']['annual_check'] / 12
            }
            
            # Calculate energy benefits
            energy_benefits = {
                'arbitrage': self.aemo_pricing.calculate_arbitrage_potential(
                    battery.capacity * battery_capacity_factor
                ),
                'fcas': self.aemo_pricing.calculate_fcas_revenue(
                    battery.capacity * battery_capacity_factor
                ),
                'demand_response': self.aemo_pricing.calculate_demand_response_revenue(
                    battery.capacity * battery_capacity_factor
                ),
                'solar_export': (solar.capacity * solar_output_factor * 4 * 30 * 0.10),  # Assuming 10c/kWh feed-in
                'power_savings': usage_profile['power_bill'] * 0.8 * (1 + 0.04) ** year,  # Assuming 4% annual increase
                'fuel_savings': usage_profile['fuel_cost'] * 0.9 * (1 + 0.03) ** year     # Assuming 3% annual increase
            }
            
            # Profit sharing calculations
            trading_revenue = energy_benefits['arbitrage'] + energy_benefits['fcas'] + energy_benefits['demand_response']
            profit_sharing = {
                'customer_share': trading_revenue * (1 - ev.profit_share - battery.profit_share),
                'ev_share': trading_revenue * ev.profit_share,
                'battery_share': trading_revenue * battery.profit_share
            }
            
            monthly_data.append({
                'month': month,
                'year': year,
                'costs': {
                    'loan_payment': monthly_payment,
                    'maintenance': sum(maintenance.values()),
                    'maintenance_breakdown': maintenance
                },
                'benefits': energy_benefits,
                'profit_sharing': profit_sharing,
                'battery_health': battery_capacity_factor * 100,
                'solar_health': solar_output_factor * 100
            })
        
        return monthly_data

def visualize_monthly_breakdown(monthly_data, month_index=0):
    """Create visualization of monthly costs and benefits"""
    fig = go.Figure()
    
    # Costs
    costs_data = monthly_data[month_index]['costs']
    benefits_data = monthly_data[month_index]['benefits']
    
    # Waterfall chart data
    measure = ['relative', 'relative', 'relative', 'relative', 'total',
               'relative', 'relative', 'relative', 'relative', 'relative', 'relative', 'total']
    
    x_data = ['Loan Payment', 'EV Maintenance', 'Solar Maintenance', 'Battery Maintenance', 'Total Costs',
              'Arbitrage', 'FCAS Revenue', 'Demand Response', 'Solar Export', 'Power Savings', 'Fuel Savings', 'Net Position']
    
    y_data = [
        -costs_data['loan_payment'],
        -costs_data['maintenance_breakdown']['ev_maintenance'],
        -costs_data['maintenance_breakdown']['solar_maintenance'],
        -costs_data['maintenance_breakdown']['battery_maintenance'],
        0,  # Total costs placeholder
        benefits_data['arbitrage'],
        benefits_data['fcas'],
        benefits_data['demand_response'],
        benefits_data['solar_export'],
        benefits_data['power_savings'],
        benefits_data['fuel_savings'],
        0   # Net position placeholder
    ]
    
    fig.add_trace(go.Waterfall(
        name="Financial Breakdown",
        orientation="v",
        measure=measure,
        x=x_data,
        y=y_data,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#E82127"}},  # Tesla red for costs
        increasing={"marker": {"color": "#000000"}},  # Black for benefits
        totals={"marker": {"color": "#808080"}},      # Grey for totals
        hovertemplate='%{x}: %{y:$,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Monthly Financial Breakdown",
        showlegend=False,
        height=500,
        yaxis_title="Amount ($)",
        xaxis_title="Components",
        font=dict(
            family="Helvetica, Arial, sans-serif",
            size=14,
            color="#000000"
        )
    )
    
    return fig

def main():
    st.set_page_config(page_title="Energy Package Designer", layout="wide")

    # Custom CSS to adjust the look and feel
    st.markdown("""
        <style>
        .css-18e3th9 {
            padding: 0;
        }
        .stButton>button {
            background-color: #E82127;
            color: #FFFFFF;
            border-radius: 5px;
            height: 3em;
            width: 100%;
            font-size: 1.2em;
        }
        .stMetric {
            font-size: 1.5em;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='font-size:48px; color:#000000;'>⚡ Energy Independence Package Designer</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#000000;'>Design your complete energy solution</h3>", unsafe_allow_html=True)
    
    # Initialize classes
    aemo = AEMOPricing()
    packages = EnergyPackages()
    roi_calc = ROICalculator(aemo)
    
    # User inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h2 style='color:#000000;'>Your Energy Profile</h2>", unsafe_allow_html=True)
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
        st.markdown("<h2 style='color:#000000;'>Recommended Package</h2>", unsafe_allow_html=True)
        st.info(
            f"Based on your profile:\n\n"
            f"🚗 EV: {recommended['ev']}\n"
            f"🔋 Battery: {recommended['battery']}\n"
            f"☀️ Solar: {recommended['solar']}"
        )
    
    # Package selection
    st.markdown("<h1 style='color:#000000;'>Package Selection</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_ev = st.selectbox(
            "Choose EV Package",
            options=list(packages.ev_packages.keys()),
            index=list(packages.ev_packages.keys()).index(recommended['ev'])
        )
        ev = packages.ev_packages[selected_ev]
        
        st.markdown(f"<h3 style='color:#000000;'>{ev.model}</h3>", unsafe_allow_html=True)
        st.write(f"🚗 **Model:** {ev.model}")
        st.write(f"⚡ **Battery Capacity:** {ev.battery_capacity} kWh")
        st.write(f"🛣️ **Range:** {ev.range} km")
        
    with col2:
        selected_battery = st.selectbox(
            "Choose Battery Package",
            options=list(packages.battery_packages.keys()),
            index=list(packages.battery_packages.keys()).index(recommended['battery'])
        )
        battery = packages.battery_packages[selected_battery]
        
        st.markdown(f"<h3 style='color:#000000;'>{selected_battery} Battery</h3>", unsafe_allow_html=True)
        st.write(f"🔋 **Capacity:** {battery.capacity} kWh")
        st.write(f"⚡ **Peak Power:** {battery.peak_power} kW")
        st.write(f"✨ **Warranty:** {battery.warranty_years} years")
        
    with col3:
        selected_solar = st.selectbox(
            "Choose Solar Package",
            options=list(packages.solar_packages.keys()),
            index=list(packages.solar_packages.keys()).index(recommended['solar'])
        )
        solar = packages.solar_packages[selected_solar]
        
        st.markdown(f"<h3 style='color:#000000;'>{selected_solar} Solar</h3>", unsafe_allow_html=True)
        st.write(f"☀️ **System Size:** {solar.capacity} kW")
        st.write(f"📊 **Panels:** {solar.panel_count} x {solar.panel_power} W")
        st.write(f"✨ **Warranty:** {solar.warranty_years} years")

    # Calculate ROI
    if st.button("Calculate Financial Benefits"):
        detailed_roi = roi_calc.calculate_detailed_roi(
            packages.ev_packages[selected_ev],
            packages.battery_packages[selected_battery],
            packages.solar_packages[selected_solar],
            usage_profile
        )
        
        # Summary metrics
        current_month_data = detailed_roi[0]
        
        st.markdown("<h1 style='color:#000000;'>Financial Summary</h1>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        total_costs = (current_month_data['costs']['loan_payment'] + 
                       current_month_data['costs']['maintenance'])
        total_benefits = sum(current_month_data['benefits'].values())
        net_monthly = total_benefits - total_costs
        
        with col1:
            st.metric(
                "Monthly Package Cost",
                f"${total_costs:,.2f}",
                help="Including loan payment and maintenance"
            )
        
        with col2:
            st.metric(
                "Monthly Benefits",
                f"${total_benefits:,.2f}",
                help="Including all energy and fuel savings"
            )
            
        with col3:
            delta_value = net_monthly - usage_profile['power_bill'] - usage_profile['fuel_cost']
            st.metric(
                "Net Monthly Position",
                f"${net_monthly:,.2f}",
                delta=f"${delta_value:,.2f} vs current"
            )
            
        with col4:
            st.metric(
                "Battery & Solar Health",
                f"{current_month_data['battery_health']:.1f}% / {current_month_data['solar_health']:.1f}%",
                help="Battery capacity / Solar output vs new"
            )
        
        # Monthly breakdown visualization
        st.markdown("<h2 style='color:#000000;'>Monthly Financial Breakdown</h2>", unsafe_allow_html=True)
        fig = visualize_monthly_breakdown(detailed_roi)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed benefits breakdown
        st.markdown("<h2 style='color:#000000;'>Energy Benefits Breakdown</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            benefits_data = current_month_data['benefits']
            for benefit, amount in benefits_data.items():
                st.metric(
                    benefit.replace('_', ' ').title(),
                    f"${amount:,.2f}"
                )
        
        with col2:
            # Create a pie chart of benefits
            fig = go.Figure(data=[go.Pie(
                labels=[benefit.replace('_', ' ').title() for benefit in benefits_data.keys()],
                values=list(benefits_data.values()),
                hole=.3,
                hovertemplate='%{label}: %{value:$,.2f}<extra></extra>'
            )])
            fig.update_layout(
                title="Benefits Distribution",
                font=dict(
                    family="Helvetica, Arial, sans-serif",
                    size=14,
                    color="#000000"
                )
            )
            st.plotly_chart(fig, use_container_width=True)

        # Package features
        st.markdown("<h2 style='color:#000000;'>Package Features</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("🚗 **EV Features**")
            for feature in ev.features:
                st.write(f"- {feature}")
                
        with col2:
            st.write("🔋 **Battery Features**")
            for feature in battery.features:
                st.write(f"- {feature}")
                
        with col3:
            st.write("☀️ **Solar Features**")
            for feature in solar.features:
                st.write(f"- {feature}")
        
        # Disclaimer
        st.markdown("---")
        st.caption(
            "Note: All calculations are estimates based on current market rates and "
            "typical usage patterns. Actual results may vary. FCAS and demand response "
            "revenues are subject to market conditions and availability."
        )

if __name__ == "__main__":
    main()
