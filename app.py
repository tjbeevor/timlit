import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px

# Data Classes
@dataclass
class EVPackage:
    model: str
    battery_capacity: float  # kWh
    range: int  # km
    charging_power: float  # kW
    v2g_capable: bool
    base_price: float
    features: List[str]

@dataclass
class BatteryPackage:
    capacity: float  # kWh
    peak_power: float  # kW
    cycles: int
    warranty_years: int
    base_price: float
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
        self.tariff_rates = {
            'peak': 0.30,        # $/kWh
            'off_peak': 0.15     # $/kWh
        }
        self.feed_in_tariff = 0.10  # $/kWh

    def calculate_arbitrage_potential(self, battery_capacity, efficiency=0.95):
        daily_cycles = 1  # Assuming one full charge/discharge per day
        daily_savings = daily_cycles * battery_capacity * efficiency * (
            self.tariff_rates['peak'] - self.tariff_rates['off_peak']
        )
        monthly_revenue = daily_savings * 30  # Approximate monthly revenue
        return monthly_revenue

class EnergyPackages:
    def __init__(self):
        self.ev_packages = {
            'Essential': EVPackage(
                model="Nissan Leaf",
                battery_capacity=40.0,
                range=270,
                charging_power=6.6,
                v2g_capable=True,
                base_price=50000 * 0.95,  # Applying a 5% discount
                features=['Vehicle-to-grid ready', 'Smart charging']
            ),
            'Performance': EVPackage(
                model="Tesla Model 3",
                battery_capacity=54.0,
                range=490,
                charging_power=11.0,
                v2g_capable=True,
                base_price=65000 * 0.95,  # Applying a 5% discount
                features=['Premium interior', '11kW AC charging', 'Autopilot']
            ),
            'Premium': EVPackage(
                model="Tesla Model Y",
                battery_capacity=75.0,
                range=505,
                charging_power=11.0,
                v2g_capable=True,
                base_price=75000 * 0.95,  # Applying a 5% discount
                features=['SUV format', 'Premium interior', 'All-wheel drive']
            )
        }

        self.battery_packages = {
            'Starter': BatteryPackage(
                capacity=6.5,
                peak_power=3.3,
                cycles=5000,
                warranty_years=10,
                base_price=7000 * 0.95,  # Applying a 5% discount
                features=['Backup power', 'Solar integration', 'Monitoring']
            ),
            'Essential': BatteryPackage(
                capacity=10.0,
                peak_power=5.0,
                cycles=6000,
                warranty_years=10,
                base_price=10000 * 0.95,  # Applying a 5% discount
                features=['Extended backup power', 'Smart monitoring']
            ),
            'Performance': BatteryPackage(
                capacity=13.5,
                peak_power=5.0,
                cycles=7000,
                warranty_years=10,
                base_price=13500 * 0.95,  # Applying a 5% discount
                features=['Whole home backup', 'Advanced monitoring']
            )
        }

        self.solar_packages = {
            'Starter': SolarPackage(
                capacity=3.3,
                panel_count=10,
                panel_power=330,
                inverter_size=3.0,
                base_price=5000 * 0.95,  # Applying a 5% discount
                warranty_years=10,
                features=['Basic monitoring']
            ),
            'Essential': SolarPackage(
                capacity=6.6,
                panel_count=20,
                panel_power=330,
                inverter_size=5.0,
                base_price=8000 * 0.95,  # Applying a 5% discount
                warranty_years=10,
                features=['Advanced monitoring', 'Panel optimization']
            ),
            'Performance': SolarPackage(
                capacity=10.0,
                panel_count=30,
                panel_power=330,
                inverter_size=8.0,
                base_price=12000 * 0.95,  # Applying a 5% discount
                warranty_years=10,
                features=['Premium panels', 'Panel optimization']
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

        # Allow for larger solar packages if roof space permits
        if roof_space >= 50:
            solar_rec = 'Performance'
        elif roof_space >= 30:
            solar_rec = 'Essential'
        else:
            solar_rec = 'Starter'

        return {
            'ev': ev_rec,
            'battery': batt_rec,
            'solar': solar_rec
        }

class ROICalculator:
    def __init__(self, aemo_pricing):
        self.aemo_pricing = aemo_pricing
        self.interest_rate = 0.035  # Reduced interest rate to 3.5% p.a.
        self.loan_term_years = 10  # Extended loan term to 10 years

        # Installation costs
        self.installation_costs = {
            'solar': {
                'base': 1000,  # Base installation fee
                'per_kw': 600,  # Additional cost per kW
                'inverter': 2000  # Inverter cost
            },
            'battery': {
                'base': 1500,  # Base installation fee
                'wiring': 1000  # Electrical work
            }
        }

        # Maintenance costs
        self.maintenance_costs = {
            'ev': {
                'annual_service': 200,  # Reduced annual service cost
                'tires': 800,  # Every 4 years
                'insurance': 1200,  # Annual insurance
                'registration': 800,  # Annual registration
                'battery_degradation': 0.01  # Reduced degradation rate to 1%
            },
            'solar': {
                'cleaning': 200,  # Annual cleaning
                'inverter_replacement': 2000,  # Every 10 years
                'degradation': 0.005  # 0.5% annual output degradation
            },
            'battery': {
                'annual_check': 150,  # Annual health check
                'degradation': 0.01,  # Reduced degradation rate to 1%
                'replacement': 10  # Expected life in years
            }
        }

    def calculate_total_installation_cost(self, solar_capacity, battery_capacity):
        solar_install = (
            self.installation_costs['solar']['base'] +
            self.installation_costs['solar']['per_kw'] * solar_capacity +
            self.installation_costs['solar']['inverter']
        )

        battery_install = (
            self.installation_costs['battery']['base'] +
            self.installation_costs['battery']['wiring']
        )

        total_cost = solar_install + battery_install
        # Subtract government rebates
        total_rebates = self.get_total_rebates(solar_capacity, battery_capacity)
        return total_cost - total_rebates

    def get_total_rebates(self, solar_capacity, battery_capacity):
        solar_rebate = solar_capacity * 700  # Increased rebate per kW
        battery_rebate = 4000  # Increased fixed battery rebate
        return solar_rebate + battery_rebate

    def calculate_monthly_payment(self, principal, years=None, rate=None):
        if years is None:
            years = self.loan_term_years
        if rate is None:
            rate = self.interest_rate
        monthly_rate = rate / 12
        months = years * 12
        return principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    def calculate_v2g_revenue(self, ev_capacity, year):
        daily_v2g_export = ev_capacity * 0.1  # Assuming 10% of capacity exported daily
        monthly_revenue = daily_v2g_export * 30 * self.aemo_pricing.feed_in_tariff
        return monthly_revenue * (1 - self.maintenance_costs['ev']['battery_degradation']) ** year

    def calculate_detailed_roi(self, ev, battery, solar, usage_profile, years=10):
        months = years * 12
        monthly_data = []

        # Calculate total system cost
        installation_cost = self.calculate_total_installation_cost(
            solar.capacity,
            battery.capacity
        )

        system_costs = {
            'ev': ev.base_price,
            'battery': battery.base_price,
            'solar': solar.base_price,
            'installation': installation_cost
        }

        total_principal = sum(system_costs.values())
        monthly_payment = self.calculate_monthly_payment(total_principal)

        for month in range(months):
            year = month / 12

            # Calculate degradation factors
            battery_capacity_factor = (1 - self.maintenance_costs['battery']['degradation']) ** year
            solar_output_factor = (1 - self.maintenance_costs['solar']['degradation']) ** year

            # Calculate maintenance costs
            maintenance = {
                'ev_maintenance': (
                    self.maintenance_costs['ev']['annual_service'] / 12 +
                    self.maintenance_costs['ev']['tires'] / (4 * 12) +  # Assuming tires every 4 years
                    self.maintenance_costs['ev']['insurance'] / 12 +
                    self.maintenance_costs['ev']['registration'] / 12
                ),
                'solar_maintenance': (
                    self.maintenance_costs['solar']['cleaning'] / 12 +
                    self.maintenance_costs['solar']['inverter_replacement'] / (10 * 12)  # Every 10 years
                ),
                'battery_maintenance': self.maintenance_costs['battery']['annual_check'] / 12
            }

            # Calculate energy benefits
            energy_benefits = {
                'arbitrage': self.aemo_pricing.calculate_arbitrage_potential(
                    battery.capacity * battery_capacity_factor
                ),
                'solar_export': (solar.capacity * solar_output_factor * 4 * 30 * self.aemo_pricing.feed_in_tariff),
                'power_savings': usage_profile['power_bill'] * 0.8 * (1 + 0.05) ** year,  # Increased to 5% annual growth
                'fuel_savings': usage_profile['fuel_cost'] * 0.9 * (1 + 0.05) ** year,  # Increased to 5% annual growth
                'v2g_revenue': self.calculate_v2g_revenue(ev.battery_capacity, year)
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
                'battery_health': battery_capacity_factor * 100,
                'solar_health': solar_output_factor * 100
            })

        return monthly_data

def visualize_monthly_breakdown(monthly_data, month_index=0):
    """Create visualization of monthly costs and benefits"""
    data = monthly_data[month_index]
    costs = data['costs']
    benefits = data['benefits']

    waterfall_data = {
        'Components': ['Loan Payment', 'EV Maintenance', 'Solar Maintenance', 'Battery Maintenance', 'Total Costs',
                       'Arbitrage', 'Solar Export', 'Power Savings', 'Fuel Savings', 'V2G Revenue', 'Total Benefits', 'Net Position'],
        'Amount': [
            -costs['loan_payment'],
            -costs['maintenance_breakdown']['ev_maintenance'],
            -costs['maintenance_breakdown']['solar_maintenance'],
            -costs['maintenance_breakdown']['battery_maintenance'],
            0,  # Placeholder for total costs
            benefits['arbitrage'],
            benefits['solar_export'],
            benefits['power_savings'],
            benefits['fuel_savings'],
            benefits['v2g_revenue'],
            0,  # Placeholder for total benefits
            0   # Placeholder for net position
        ],
        'Measure': ['relative'] * 4 + ['total'] + ['relative'] * 5 + ['total', 'total']
    }

    # Calculate totals
    total_costs = sum(waterfall_data['Amount'][:4])
    waterfall_data['Amount'][4] = total_costs

    total_benefits = sum(waterfall_data['Amount'][5:10])
    waterfall_data['Amount'][10] = total_benefits

    net_position = total_costs + total_benefits
    waterfall_data['Amount'][11] = net_position

    fig = go.Figure(go.Waterfall(
        x=waterfall_data['Components'],
        y=waterfall_data['Amount'],
        measure=waterfall_data['Measure'],
        text=[f"${x:,.2f}" for x in waterfall_data['Amount']],
        textposition="outside",
        decreasing={"marker": {"color": "#E82127"}},
        increasing={"marker": {"color": "#000000"}},
        totals={"marker": {"color": "#808080"}},
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
    .css-18e3th9 {padding: 0;}
    .stButton>button {
        background-color: #E82127;
        color: #FFFFFF;
        border-radius: 5px;
        height: 3em;
        width: 100%;
        font-size: 1.2em;
    }
    .stMetric {font-size: 1.5em;}
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
        power_bill = st.number_input("Monthly Power Bill ($)", min_value=0.0, value=250.0)
        fuel_cost = st.number_input("Monthly Fuel Cost ($)", min_value=0.0, value=200.0)
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
            f"🚗 **EV:** {recommended['ev']}\n"
            f"🔋 **Battery:** {recommended['battery']}\n"
            f"☀️ **Solar:** {recommended['solar']}"
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
        st.write(f"✨ **Features:**")
        for feature in ev.features:
            st.write(f"- {feature}")

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
        st.write(f"✨ **Features:**")
        for feature in battery.features:
            st.write(f"- {feature}")

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
        st.write(f"✨ **Features:**")
        for feature in solar.features:
            st.write(f"- {feature}")

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
            delta_value = net_monthly - (usage_profile['power_bill'] + usage_profile['fuel_cost'])
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
            labels = [benefit.replace('_', ' ').title() for benefit in benefits_data.keys()]
            values = list(benefits_data.values())
            fig = px.pie(
                names=labels,
                values=values,
                title="Benefits Distribution",
                hole=0.4
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
            "typical usage patterns. Actual results may vary. Government rebates are included in the calculations."
        )

if __name__ == "__main__":
    main()
