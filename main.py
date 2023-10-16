# Sri Lanka Tank rejuvenation priority index
# This script generates an agricultural dependent population shapefile and attributes
# agricltural dependent population to water tanks to determine the serviced population
# of each tank. The higher the population, the higher the priority of the tank.

# Import phase
import datetime
import pytz
tz_London = pytz.timezone('Europe/London')
now = datetime.datetime.now(tz_London)
print ("Program started at: ", now.strftime("%H:%M:%S"), "(London time)")


print("All packages imported")