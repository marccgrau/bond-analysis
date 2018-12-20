# -*- coding: utf-8 -*-
"""

@author: marcg

"""
import sys
import pandas as pd
import quandl
import numpy as np
import matplotlib.pyplot as plt

# To get the data for the forward rates please enter your Quandl API Key
quandl.ApiConfig.api_key = "ZzyxEEkVxNqQBKE9jXYd"

##################
### User Input ###
##################

# strings defined as possible answers for the following questions
yes = {'YES', 'Yes', 'Y','yes','y', 'ye', ''}
no = {'NO', 'No', 'N', 'no','n'}

# In this stage the user is asked wether he wants to provide the price himself or let the program calculate it
# depending on the answer different mechanisms are triggered
# if he doesn't provide a suitable answer, he will be asked the same question again
print("What kind of analysis do you want to do? (y/n)")
print("yes - if you want to do calculations based on a given price")
print("no - if you want to calculate a fair price based on coupon and maturity (neglecting risks)")
choice = str(input().lower())
if choice in yes:
   choice = True
elif choice in no:
   choice = False
else:
   sys.stdout.write("Please respond with 'yes' or 'no'")

# depending on the previous choice one flow to ask for inputs is triggered
# if the price is not known yet we only have to ask for the coupon and the time to maturity. Everything else will be calculated
# if the price and face value are given as input we store them and ask the same questions as in the other case
# if the answers aren't suitable to the program the user will be asked again or in case of an input of the wrong format he will be told to change 
if choice == False:
    coupon = -1
    while 0 > coupon or 50 < coupon:
        try:
            coupon = float(input("Please enter the coupon of your bond (in percentage): "))
        except ValueError:
            print("Unfortunately, this program doesn't cover negative coupons or coupons above 50% as it appears unrealistic. Please enter another coupon.")
    T = 0
    while 1 >= T or 30 <= T:
        try:
            T = int(input("Please enter the remaining years until the bond matures: "))
        except ValueError:
            print("We're sorry. This program only uses yield curve estimates between 1 to 30 years. Please remain in this boundaries")
else:
    input_price = float(input("Please enter the price of your bond: "))
    input_fv = float(input("Please enter the face value of your bond: "))
    coupon = -1
    while 0 > coupon or 50 < coupon:
        try:
            coupon = float(input("Please enter the coupon of your bond (in percentage): "))
        except ValueError:
            print("Unfortunately, this program doesn't cover negative coupons or coupons above 50% as it appears unrealistic. Please enter another coupon.")
    T = 0
    while 1 >= T or 30 <= T:
        try:
            T = int(input("Please enter the remaining years until the bond matures: "))
        except ValueError:
            print("We're sorry. This program only uses yield curve estimates between 1 to 30 years. Please remain in this boundaries")    

###################
### Needed Data ###
###################


# in order to have an estimate for the forward rates we retrieve some data from Quandl
# This curve, which relates the yield on a security to its time to maturity is based on the closing 
# market bid yields on actively traded Treasury securities in the over-the-counter market. 
# These market yields are calculated from composites of quotations obtained by the Federal Reserve Bank of New York. 
# The yield values are read from the yield curve at fixed maturities, currently 1, 2, 3, 5, 7, 10, 20, and 30 years. 
# We always use the most recent estimations in this program
UStreasury = quandl.get("USTREASURY/YIELD", limit = 1)

UStreasury_yields = UStreasury.iloc[:,4:12]

US_1y = float(UStreasury_yields.iloc[0,0])
US_2y = float(UStreasury_yields.iloc[0,1])
US_3y = float(UStreasury_yields.iloc[0,2])
US_5y = float(UStreasury_yields.iloc[0,3])
US_7y = float(UStreasury_yields.iloc[0,4])
US_10y = float(UStreasury_yields.iloc[0,5])
US_20y = float(UStreasury_yields.iloc[0,6])
US_30y = float(UStreasury_yields.iloc[0,7])

# Very simple extrapolation to have the forward rates of the missing years
# For more sophisticated analysis yield curve simulations (e.g. Vasicek-Model) could be implemented
# In this case we assume a linear relation between the known values of the yield curve
g_7 = (US_10y - US_7y)/3
g_10 = (US_20y - US_10y)/10
g_20 = (US_30y - US_20y)/10

US_4y = (US_3y + US_5y)/2
US_6y = (US_5y + US_7y)/2
US_8y = US_7y + g_7
US_9y = US_7y + 2*g_7
US_11y = US_10y + g_10
US_12y = US_10y + 2*g_10
US_13y = US_10y + 3*g_10
US_14y = US_10y + 4*g_10
US_15y = US_10y + 5*g_10
US_16y = US_10y + 6*g_10
US_17y = US_10y + 7*g_10
US_18y = US_10y + 8*g_10
US_19y = US_10y + 9*g_10
US_21y = US_20y + g_20
US_22y = US_20y + 2*g_20
US_23y = US_20y + 3*g_20
US_24y = US_20y + 4*g_20
US_25y = US_20y + 5*g_20
US_26y = US_20y + 6*g_20
US_27y = US_20y + 7*g_20
US_28y = US_20y + 8*g_20
US_29y = US_20y + 9*g_20

forward_rates = np.array([US_1y, US_2y, US_3y, US_4y, US_5y, US_6y, US_7y, US_8y, US_9y, US_10y, US_11y, US_12y, US_13y, US_14y, US_15y, US_16y, US_17y, US_18y, US_19y, US_20y, US_21y, US_22y, US_23y, US_24y, US_25y, US_26y, US_27y, US_28y, US_29y, US_30y])

# depending on the years to maturity of the bond we're choosing the respective timeframe of the forward rates
fr = forward_rates[0:T]

# to unify the numbers for the calculations we don't caluclate in percentage points
# the face value is standardized to 1
# a fixed value of 0.1 is set to start the calculations of the newton process
if choice == True:
    fv = input_fv
else:
    fv = int(1)

coupon = coupon/100
fr = fr/100
m = np.arange(1,T+1)
cfs = [coupon*fv]*(T-1) + [fv+(coupon*fv)]
initialGuess = 0.1

###############################
### Definition of functions ###
###############################

### All coupon payments are assumed to be reinvested at the possible returns at this time

# calculation of the bond price using the 
def BondPrice(fr, cfs, m):
    cfs_disc = cfs/((1+fr)**m)
    bondprice = np.sum(cfs_disc)
    return(bondprice)

if choice == True:
    bondprice = input_price
else:
    bondprice = BondPrice(fr,cfs,m)

# calculation of dollar duration, modified duration and macaulay duration
def BondDuration(bondprice, cfs, m, ytm):
        dur_cfs_disc = (cfs*m)/((1+ytm)**(m+1))
        dur = np.sum(dur_cfs_disc)
        mod_dur = dur/bondprice
        mac_dur = dur*(1+ytm)/bondprice
        durations = [dur, mod_dur, mac_dur]
        return(durations)

# function to calculate ytm via newton process
def f(x):
    y_1 = -bondprice + (coupon*fv)*((1 - (1 + x)**-T)/x) + fv*(1 + x)**-T
    return(y_1)

# first order derivative of f(x)
def f_der(x):
    y_2 = (coupon*fv)*((x*T*((1 + x)**(-T-1)) - (1 - ((1 + x)**-T)))/(x**2)) - fv*T*((1+x)**(-T-1))
    return(y_2)

# the newton-raphson process is a method for finding successively better approximations to the roots (or zeroes) of a real-valued function
def Newton(x_i):
    x_i = x_i - f(x_i)/f_der(x_i)
    return(x_i)

# using the defined formula from above we approximate the yield to maturity of the bond
def YieldToMaturity(initialGuess):
    error = 0.000000001
    x_i = initialGuess
    delta = 1
    global count
    count = 0
    while delta > error:
        x_i_next = Newton(x_i)
        count = count + 1
        delta = abs(x_i_next - x_i)
        x_i = x_i_next
    return(x_i)

# Specifiying the plot
xlimit = [1,T]
ylimit = [0, round((max(fr)*100)+0.5, 2)]

plt.xlim(xlimit)
plt.ylim(ylimit)
plt.xlabel('Years')
plt.ylabel('Interest Rate')
plt.plot(m,fr*100)

# applying the functions with the given input data we receive the following results
ytm = round(YieldToMaturity(initialGuess), 4)
durations = BondDuration(bondprice, cfs, m, ytm)

print('Input parameters are: ')
print('Coupon:              ', round(100*coupon),'%')
print('Time to maturity:    ', T, ' years')
print('')
print('Spot & Forward Rates:', fr)

print('')
print('This plot shows the development of the rates over time:')
plt.show()
print('')
print('Results:')
if choice == True:
    print('The price you have given as an input: ', bondprice)
else:
    print('Given the parameters your bond should currently be priced the following: ', round(bondprice, 2))
print('The yield to maturity of your bond is: ', round(100*ytm, 2), '%')
print('YTM was calculated doing ', count,' iterations.')
print('')
print('Your Bond has the following durations:')
print('Modified duration:   ', round(durations[1], 2))
print('Macaulay duration:   ', round(durations[2], 2))

