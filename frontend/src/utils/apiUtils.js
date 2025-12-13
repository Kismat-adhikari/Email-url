/**
 * API Usage Utilities
 * Centralized formatting and tier logic for consistent display across the app
 */

// Tier configurations - keep in sync with backend
export const TIER_CONFIGS = {
  free: {
    name: 'Free',
    apiLimit: 10, // 10 per day
    limitType: 'daily', // daily reset
    features: {
      batchValidation: false,
      emailSending: false
    }
  },
  starter: {
    name: 'Starter', 
    apiLimit: 10000, // 10K per month
    limitType: 'monthly', // monthly reset
    features: {
      batchValidation: true,
      emailSending: false
    }
  },
  pro: {
    name: 'Pro',
    apiLimit: 10000000, // 10 million lifetime
    limitType: 'lifetime', // never resets
    features: {
      batchValidation: true,
      emailSending: true
    }
  }
};

/**
 * Format API usage numbers for display
 * @param {number} used - Number of API calls used
 * @param {number} limit - API call limit from database
 * @param {string} tier - User's subscription tier
 * @returns {string} Formatted string like "1.5K/10M"
 */
export const formatApiUsage = (used, limit, tier) => {
  // Format used count
  const formatUsed = used >= 1000000 ? `${(used / 1000000).toFixed(1)}M` : 
                    used >= 1000 ? `${(used / 1000).toFixed(1)}K` : 
                    used.toString();
  
  // Get the correct limit for the tier (override database value if needed)
  const correctLimit = getCorrectApiLimit(tier);
  const formatLimit = correctLimit >= 1000000 ? `${(correctLimit / 1000000).toFixed(0)}M` :
                     correctLimit >= 1000 ? `${(correctLimit / 1000).toFixed(0)}K` : 
                     correctLimit.toString();
  
  return `${formatUsed}/${formatLimit}`;
};

/**
 * Get the correct API limit for a tier (handles legacy database values)
 * @param {string} tier - User's subscription tier
 * @returns {number} Correct API limit for the tier
 */
export const getCorrectApiLimit = (tier) => {
  const config = TIER_CONFIGS[tier];
  return config ? config.apiLimit : 10; // Default to free tier if unknown
};

/**
 * Format API limit for display (without usage)
 * @param {string} tier - User's subscription tier
 * @returns {string} Formatted limit like "10M lifetime" or "10K/month"
 */
export const formatApiLimit = (tier) => {
  const config = TIER_CONFIGS[tier];
  if (!config) return '10';
  
  const limit = config.apiLimit;
  let formattedLimit;
  
  if (limit >= 1000000) {
    formattedLimit = `${(limit / 1000000).toFixed(0)}M`;
  } else if (limit >= 1000) {
    formattedLimit = `${(limit / 1000).toFixed(0)}K`;
  } else {
    formattedLimit = limit.toString();
  }
  
  // Add period indicator
  switch (config.limitType) {
    case 'daily':
      return `${formattedLimit}/day`;
    case 'monthly':
      return `${formattedLimit}/month`;
    case 'lifetime':
      return `${formattedLimit} lifetime`;
    default:
      return formattedLimit;
  }
};

/**
 * Get tier display name
 * @param {string} tier - User's subscription tier
 * @returns {string} Display name like "Pro" or "Starter"
 */
export const getTierDisplayName = (tier) => {
  const config = TIER_CONFIGS[tier];
  return config ? config.name : 'Free';
};

/**
 * Check if tier has a specific feature
 * @param {string} tier - User's subscription tier
 * @param {string} feature - Feature to check ('batchValidation' or 'emailSending')
 * @returns {boolean} Whether the tier has the feature
 */
export const tierHasFeature = (tier, feature) => {
  const config = TIER_CONFIGS[tier];
  return config ? config.features[feature] : false;
};

/**
 * Get usage percentage
 * @param {number} used - Number of API calls used
 * @param {string} tier - User's subscription tier
 * @returns {number} Usage percentage (0-100)
 */
export const getUsagePercentage = (used, tier) => {
  const limit = getCorrectApiLimit(tier);
  return Math.min((used / limit) * 100, 100);
};

/**
 * Get the limit type for a tier
 * @param {string} tier - User's subscription tier
 * @returns {string} Limit type ('daily', 'monthly', 'lifetime')
 */
export const getLimitType = (tier) => {
  const config = TIER_CONFIGS[tier];
  return config ? config.limitType : 'daily';
};

/**
 * Format API usage with period indicator
 * @param {number} used - Number of API calls used
 * @param {number} limit - API call limit from database
 * @param {string} tier - User's subscription tier
 * @returns {string} Formatted string like "5/10 today" or "1.5K/10M lifetime"
 */
export const formatApiUsageWithPeriod = (used, limit, tier) => {
  const config = TIER_CONFIGS[tier];
  if (!config) return formatApiUsage(used, limit, tier);
  
  const basicFormat = formatApiUsage(used, limit, tier);
  
  switch (config.limitType) {
    case 'daily':
      return `${basicFormat} today`;
    case 'monthly':
      return `${basicFormat} this month`;
    case 'lifetime':
      return `${basicFormat} lifetime`;
    default:
      return basicFormat;
  }
};