// Dictionary for mapping technical keys to user-friendly labels
export const keyMapping = {
  // Lighting inconsistencies
  mean_local_variance: 'Mean Local Variance',
  std_local_variance: 'Standard Local Variance',

  // Regional Noise Variations
  region_0_0: 'Top-Left Region',
  region_0_1: 'Top-Right Region',
  region_1_0: 'Bottom-Left Region',
  region_1_1: 'Bottom-Right Region'
};

// Utility function to apply mapping to an object or array of objects
export const mapKeysToLabels = (data) => {
  if (Array.isArray(data)) {
    return data.map(item => {
      const key = Object.keys(item)[0];
      const value = item[key];
      const newKey = keyMapping[key] || key;
      return { [newKey]: value };
    });
  } else if (typeof data === 'object' && data !== null) {
    return Object.fromEntries(
      Object.entries(data).map(([key, value]) => [
        keyMapping[key] || key,
        value
      ])
    );
  }
  return data;
};
