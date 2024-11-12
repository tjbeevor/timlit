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
class ICEVehicle:
    base_price: float
    fuel_consumption: float  # L/100km
    annual_service: float
    depreciation_rate: float
    insurance: float
    registration: float

@dataclass
class TaxBenefits:
    gst_rate: float = 0.10
    fbt_rate: float = 0.47
    business_use_percentage: float = 0.80
    tax_bracket: float = 0.37


@dataclass
class EVPackage:
    model: str
    battery_capacity: float  # kWh
    range: int  # km
    charging_power: float  # kW
    v2g_capable: bool
    base_price: float
    features: List[str]
    depreciation_rate: float  # Annual depreciation rate (%)
    energy_consumption_per_km: float  # kWh per km

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
                features=['Vehicle-to-grid ready', 'Smart charging'],
                depreciation_rate=15.0,  # 15% annual depreciation
                energy_consumption_per_km=0.15  # kWh per km
            ),
            'Performance': EVPackage(
                model="Tesla Model 3",
                battery_capacity=54.0,
                range=490,
                charging_power=11.0,
                v2g_capable=True,
                base_price=65000 * 0.95,  # Applying a 5% discount
                features=['Premium interior', '11kW AC charging', 'Autopilot'],
                depreciation_rate=12.0,  # 12% annual depreciation
                energy_consumption_per_km=0.14  # kWh per km
            ),
            'Premium': EVPackage(
                model="Tesla Model Y",
                battery_capacity=75.0,
                range=505,
                charging_power=11.0,
                v2g_capable=True,
                base_price=75000 * 0.95,  # Applying a 5% discount
                features=['SUV format', 'Premium interior', 'All-wheel drive'],
                depreciation_rate=10.0,  # 10% annual depreciation
                energy_consumption_per_km=0.16  # kWh per km
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
    def __init__(self, aemo_pricing, interest_rate, loan_term_years, installation_costs, 
                 maintenance_costs, solar_rebate_per_kw, battery_rebate, 
                 power_price_inflation, fuel_price_inflation):
        # Existing initializations...
        self.ice_vehicle = ICEVehicle(
            base_price=45000,
            fuel_consumption=8.5,
            annual_service=800,
            depreciation_rate=0.15,
            insurance=1000,
            registration=800
        )
        self.tax_benefits = TaxBenefits()
    
    def calculate_tax_benefits(self, ev_price, year):
        """Calculate GST and FBT benefits"""
        if year < 5:
            # First vehicle
            gst_benefit = ev_price * self.tax_benefits.gst_rate * self.tax_benefits.business_use_percentage
            fbt_base = ev_price * self.tax_benefits.business_use_percentage
            fbt_benefit = fbt_base * self.tax_benefits.fbt_rate * (1 - self.tax_benefits.business_use_percentage)
        else:
            # Second vehicle
            new_ev_price = ev_price * (1 + 0.10)  # Assuming 10% price increase for new model
            gst_benefit = new_ev_price * self.tax_benefits.gst_rate * self.tax_benefits.business_use_percentage
            fbt_base = new_ev_price * self.tax_benefits.business_use_percentage
            fbt_benefit = fbt_base * self.tax_benefits.fbt_rate * (1 - self.tax_benefits.business_use_percentage)
        
        return {
            'gst_benefit': gst_benefit / 12,  # Monthly benefit
            'fbt_benefit': fbt_benefit / 12
        }

    def calculate_detailed_roi(self, ev, battery, solar, usage_profile, years=10):
        monthly_data = []
        
        # Initial vehicle costs
        ev_initial = ev.base_price
        ice_initial = self.ice_vehicle.base_price
        
        # First EV loan
        ev_loan_schedule = self.generate_amortization_schedule(
            principal=ev_initial,
            annual_interest_rate=self.interest_rate,
            loan_term_years=5  # 5-year loan for first vehicle
        )
        
        for month in range(years * 12):
            year = month / 12
            
            # Handle vehicle replacement at year 5
            if month == 60:  # 5 years
                # Calculate trade-in values
                ev_trade_in = ev_initial * ((1 - ev.depreciation_rate) ** 5)
                ice_trade_in = ice_initial * ((1 - self.ice_vehicle.depreciation_rate) ** 5)
                
                # New EV purchase with trade-in
                new_ev_price = ev.base_price * 1.10  # Assuming 10% price increase
                ev_loan_schedule = self.generate_amortization_schedule(
                    principal=new_ev_price - ev_trade_in,
                    annual_interest_rate=self.interest_rate,
                    loan_term_years=5
                )
            
            # Calculate tax benefits
            tax_benefits = self.calculate_tax_benefits(ev.base_price, year)
            
            # Rest of the existing calculations...
            # Add tax benefits to the monthly data
            monthly_data.append({
                'month': month,
                'year': year,
                'tax_benefits': tax_benefits,
                # ... rest of the existing data
            })
        
        return monthly_data

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
        solar_rebate = solar_capacity * self.solar_rebate_per_kw
        battery_rebate = self.battery_rebate
        return solar_rebate + battery_rebate

    def generate_amortization_schedule(self, principal, annual_interest_rate, loan_term_years):
        schedule = []
        monthly_interest_rate = annual_interest_rate / 12
        months = loan_term_years * 12
        monthly_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate) ** months) / ((1 + monthly_interest_rate) ** months - 1)
        remaining_principal = principal

        for month in range(1, months + 1):
            interest_payment = remaining_principal * monthly_interest_rate
            principal_payment = monthly_payment - interest_payment
            remaining_principal -= principal_payment
            schedule.append({
                'month': month,
                'interest_payment': interest_payment,
                'principal_payment': principal_payment,
                'remaining_principal': remaining_principal,
                'total_payment': monthly_payment
            })
        return schedule

    def calculate_detailed_roi(self, ev, battery, solar, usage_profile, years=10):
        months = years * 12
        monthly_data = []

        # Calculate total system cost
        installation_cost = self.calculate_total_installation_cost(
            solar.capacity,
            battery.capacity
        )

        system_costs = {
            'battery': battery.base_price,
            'solar': solar.base_price,
            'installation': installation_cost
        }

        total_principal = sum(system_costs.values())

        # Generate amortization schedule for the solar/battery loan
        loan_schedule = self.generate_amortization_schedule(
            principal=total_principal,
            annual_interest_rate=self.interest_rate,
            loan_term_years=self.loan_term_years
        )

        # Initial EV purchase
        ev_principal = ev.base_price

        # Generate amortization schedule for the EV loan
        ev_loan_schedule = self.generate_amortization_schedule(
            principal=ev_principal,
            annual_interest_rate=self.interest_rate,
            loan_term_years=self.loan_term_years
        )

        # Prepare for EV replacement at year 5
        ev_replacement_month = 5 * 12  # Replace at month 60

        for month in range(months):
            year = month / 12

            # Handle EV replacement
            if month == ev_replacement_month:
                # Calculate depreciated value of old EV
                old_ev_value = ev.base_price * ((1 - ev.depreciation_rate / 100) ** 5)
                # Assume selling the old EV
                trade_in_value = old_ev_value

                # Purchase new EV
                ev_principal = ev.base_price - trade_in_value  # Subtract trade-in value
                # Generate new EV loan schedule
                ev_loan_schedule = self.generate_amortization_schedule(
                    principal=ev_principal,
                    annual_interest_rate=self.interest_rate,
                    loan_term_years=self.loan_term_years
                )
                ev_loan_start_month = month  # New EV loan starts now

            # Get loan payments
            if month < len(loan_schedule):
                loan_payment_info = loan_schedule[month]
                loan_payment = loan_payment_info['total_payment']
                loan_interest = loan_payment_info['interest_payment']
                loan_principal = loan_payment_info['principal_payment']
            else:
                loan_payment = 0
                loan_interest = 0
                loan_principal = 0

            # EV loan payments
            if month < len(ev_loan_schedule):
                ev_loan_payment_info = ev_loan_schedule[month]
                ev_loan_payment = ev_loan_payment_info['total_payment']
                ev_loan_interest = ev_loan_payment_info['interest_payment']
                ev_loan_principal = ev_loan_payment_info['principal_payment']
            else:
                ev_loan_payment = 0
                ev_loan_interest = 0
                ev_loan_principal = 0

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

            # Calculate EV energy consumption
            monthly_km_driven = usage_profile['daily_commute'] * 30  # Assuming 30 days per month
            monthly_ev_energy_consumption = monthly_km_driven * ev.energy_consumption_per_km  # kWh per month

            # Calculate cost of charging EV
            solar_ev_charging_percentage = 0.5  # 50% charged from solar
            solar_ev_energy_consumption = monthly_ev_energy_consumption * solar_ev_charging_percentage
            grid_ev_energy_consumption = monthly_ev_energy_consumption * (1 - solar_ev_charging_percentage)

            # Cost of solar charging is opportunity cost (feed-in tariff)
            solar_ev_charging_cost = solar_ev_energy_consumption * self.aemo_pricing.feed_in_tariff
            # Cost of grid charging at off-peak rates
            grid_ev_charging_cost = grid_ev_energy_consumption * self.aemo_pricing.tariff_rates['off_peak']

            total_ev_charging_cost = solar_ev_charging_cost + grid_ev_charging_cost

            # Calculate energy benefits
            energy_benefits = {
                'arbitrage': self.aemo_pricing.calculate_arbitrage_potential(
                    battery.capacity * battery_capacity_factor
                ),
                'solar_export': (solar.capacity * solar_output_factor * 4 * 30 * self.aemo_pricing.feed_in_tariff),
                'power_savings': usage_profile['power_bill'] * 0.8 * (1 + self.power_price_inflation) ** year,
                'fuel_savings': usage_profile['fuel_cost'] * (1 + self.fuel_price_inflation) ** year,
                'v2g_revenue': self.aemo_pricing.feed_in_tariff * ev.battery_capacity * 0.1 * 30,
            }

            # Net fuel savings after accounting for EV charging cost
            net_fuel_savings = energy_benefits['fuel_savings'] - total_ev_charging_cost

            total_benefits = sum(energy_benefits.values()) - total_ev_charging_cost  # Subtract EV charging cost

            total_costs = loan_payment + ev_loan_payment + sum(maintenance.values())

            net_position = total_benefits - total_costs

            monthly_data.append({
                'month': month,
                'year': year,
                'costs': {
                    'loan_payment': loan_payment,
                    'ev_loan_payment': ev_loan_payment,
                    'maintenance': sum(maintenance.values()),
                    'maintenance_breakdown': maintenance,
                    'ev_charging_cost': total_ev_charging_cost
                },
                'benefits': energy_benefits,
                'net_fuel_savings': net_fuel_savings,
                'battery_health': battery_capacity_factor * 100,
                'solar_health': solar_output_factor * 100,
                'net_position': net_position
            })

        return monthly_data

def visualize_monthly_breakdown(monthly_data, month_index=0):
    """Create visualization of monthly costs and benefits"""
    data = monthly_data[month_index]
    costs = data['costs']
    benefits = data['benefits']

    waterfall_data = {
        'Components': ['Loan Payment', 'EV Loan Payment', 'EV Charging Cost', 'EV Maintenance', 'Solar Maintenance', 'Battery Maintenance', 'Total Costs',
                       'Arbitrage', 'Solar Export', 'Power Savings', 'Fuel Savings', 'V2G Revenue', 'Total Benefits', 'Net Position'],
        'Amount': [
            -costs['loan_payment'],
            -costs['ev_loan_payment'],
            -costs['ev_charging_cost'],
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
        'Measure': ['relative'] * 6 + ['total'] + ['relative'] * 5 + ['total', 'total']
    }

    # Calculate totals
    total_costs = sum(waterfall_data['Amount'][:6])
    waterfall_data['Amount'][6] = total_costs

    total_benefits = sum(waterfall_data['Amount'][7:12])
    waterfall_data['Amount'][12] = total_benefits

    net_position = total_costs + total_benefits
    waterfall_data['Amount'][13] = net_position

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

    with st.expander("Vehicle and Tax Settings"):
        st.markdown("#### ICE Vehicle Comparison")
        ice_price = st.number_input("ICE Vehicle Base Price ($)", value=45000)
        ice_fuel_consumption = st.number_input("Fuel Consumption (L/100km)", value=8.5)
        ice_depreciation = st.number_input("Annual Depreciation Rate (%)", value=15.0)
        
        st.markdown("#### Tax Benefits")
        business_use = st.slider("Business Use Percentage (%)", 0, 100, 80)
        tax_bracket = st.selectbox("Tax Bracket (%)", [0, 19, 32.5, 37, 45])

    # Editable assumptions
    st.markdown("<h1 style='color:#000000;'>Financial Summary</h1>", unsafe_allow_html=True)
    with st.expander("Adjust Assumptions"):
        st.markdown("#### Financial Assumptions")
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.1)
        loan_term_years = st.number_input("Loan Term (years)", min_value=1, max_value=30, value=10)

        st.markdown("#### Installation Costs")
        solar_base_install = st.number_input("Solar Base Installation Cost ($)", min_value=0, value=1000)
        solar_per_kw = st.number_input("Solar Installation Cost per kW ($)", min_value=0, value=600)
        solar_inverter_cost = st.number_input("Solar Inverter Cost ($)", min_value=0, value=2000)

        battery_base_install = st.number_input("Battery Base Installation Cost ($)", min_value=0, value=1500)
        battery_wiring_cost = st.number_input("Battery Wiring Cost ($)", min_value=0, value=1000)

        st.markdown("#### Maintenance Costs")
        ev_annual_service = st.number_input("EV Annual Service Cost ($)", min_value=0, value=200)
        ev_tires_cost = st.number_input("EV Tires Replacement Cost ($)", min_value=0, value=800)
        ev_insurance = st.number_input("EV Annual Insurance Cost ($)", min_value=0, value=1200)
        ev_registration = st.number_input("EV Annual Registration Cost ($)", min_value=0, value=800)
        solar_cleaning = st.number_input("Solar Annual Cleaning Cost ($)", min_value=0, value=200)
        solar_inverter_replacement = st.number_input("Solar Inverter Replacement Cost ($)", min_value=0, value=2000)
        battery_annual_check = st.number_input("Battery Annual Check Cost ($)", min_value=0, value=150)

        st.markdown("#### Degradation Rates")
        ev_battery_degradation = st.number_input("EV Battery Degradation Rate (% per year)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        solar_degradation = st.number_input("Solar Output Degradation Rate (% per year)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
        battery_degradation = st.number_input("Battery Degradation Rate (% per year)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)

        st.markdown("#### Energy Price Inflation Rates")
        power_price_inflation = st.number_input("Power Price Inflation Rate (% per year)", min_value=0.0, max_value=10.0, value=5.0, step=0.1)
        fuel_price_inflation = st.number_input("Fuel Price Inflation Rate (% per year)", min_value=0.0, max_value=10.0, value=5.0, step=0.1)

        st.markdown("#### Government Rebates")
        solar_rebate_per_kw = st.number_input("Solar Rebate per kW ($)", min_value=0, value=700)
        battery_rebate = st.number_input("Battery Rebate ($)", min_value=0, value=4000)

    # Create installation_costs and maintenance_costs dictionaries
    installation_costs = {
        'solar': {
            'base': solar_base_install,
            'per_kw': solar_per_kw,
            'inverter': solar_inverter_cost
        },
        'battery': {
            'base': battery_base_install,
            'wiring': battery_wiring_cost
        }
    }

    maintenance_costs = {
        'ev': {
            'annual_service': ev_annual_service,
            'tires': ev_tires_cost,
            'insurance': ev_insurance,
            'registration': ev_registration,
            'battery_degradation': ev_battery_degradation / 100.0  # Convert to decimal
        },
        'solar': {
            'cleaning': solar_cleaning,
            'inverter_replacement': solar_inverter_replacement,
            'degradation': solar_degradation / 100.0  # Convert to decimal
        },
        'battery': {
            'annual_check': battery_annual_check,
            'degradation': battery_degradation / 100.0  # Convert to decimal
        }
    }

    # Create an instance of ROICalculator with the user-provided values
    roi_calc = ROICalculator(
        aemo_pricing=aemo,
        interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        installation_costs=installation_costs,
        maintenance_costs=maintenance_costs,
        solar_rebate_per_kw=solar_rebate_per_kw,
        battery_rebate=battery_rebate,
        power_price_inflation=power_price_inflation,
        fuel_price_inflation=fuel_price_inflation
    )

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

        col1, col2, col3, col4 = st.columns(4)

        total_costs = (current_month_data['costs']['loan_payment'] +
                       current_month_data['costs']['ev_loan_payment'] +
                       current_month_data['costs']['maintenance'] +
                       current_month_data['costs']['ev_charging_cost'])
        total_benefits = sum(current_month_data['benefits'].values())
        net_monthly = total_benefits - total_costs

        with col1:
            st.metric(
                "Monthly Package Cost",
                f"${total_costs:,.2f}",
                help="Including loan payments, EV charging, and maintenance"
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

        # Create DataFrame for plotting over time
        df_roi = pd.DataFrame(detailed_roi)
        df_roi['total_costs'] = df_roi['costs'].apply(lambda x: x['loan_payment'] + x['ev_loan_payment'] + x['maintenance'] + x['ev_charging_cost'])
        df_roi['total_benefits'] = df_roi['benefits'].apply(lambda x: sum(x.values()))
        df_roi['net_position'] = df_roi['net_position']
        df_roi['cumulative_net_position'] = df_roi['net_position'].cumsum()
        df_roi['year'] = df_roi['year']

        # Plot cumulative net position over time
        st.markdown("<h2 style='color:#000000;'>Cumulative Net Position Over Time</h2>", unsafe_allow_html=True)
        fig_cumulative = px.line(
            df_roi,
            x='year',
            y='cumulative_net_position',
            title='Cumulative Net Position Over Time',
            labels={'year': 'Year', 'cumulative_net_position': 'Cumulative Net Position ($)'}
        )
        st.plotly_chart(fig_cumulative, use_container_width=True)

        # Plot annual total costs and benefits over time
        st.markdown("<h2 style='color:#000000;'>Annual Costs and Benefits Over Time</h2>", unsafe_allow_html=True)
        df_roi['year_int'] = df_roi['year'].astype(int)
        df_annual = df_roi.groupby('year_int').agg({
            'total_costs': 'sum',
            'total_benefits': 'sum'
        }).reset_index()

        fig_annual = go.Figure()
        fig_annual.add_trace(go.Bar(
            x=df_annual['year_int'],
            y=df_annual['total_benefits'],
            name='Total Benefits',
            marker_color='green'
        ))
        fig_annual.add_trace(go.Bar(
            x=df_annual['year_int'],
            y=-df_annual['total_costs'],  # Negative for costs
            name='Total Costs',
            marker_color='red'
        ))
        fig_annual.update_layout(
            title='Annual Total Costs and Benefits',
            xaxis_title='Year',
            yaxis_title='Amount ($)',
            barmode='group'
        )
        st.plotly_chart(fig_annual, use_container_width=True)

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
