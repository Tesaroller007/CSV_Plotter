import numpy as np
import matplotlib.pyplot as plt

# Create x values from 0 to 4π
x = np.linspace(0, 4*np.pi, 200)

# Calculate sine values
y = np.sin(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', label='sin(x)')
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.legend()

# Display the plot
plt.show()