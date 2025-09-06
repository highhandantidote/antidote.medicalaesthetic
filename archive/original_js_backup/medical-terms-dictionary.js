/**
 * Medical terminology dictionary for search term enhancement
 * Maps common terms to their medical equivalents and related procedures
 */

const medicalTermsDictionary = {
    // Procedure name mappings (common terms to medical terms)
    "nose job": ["rhinoplasty", "septoplasty", "septorhinoplasty", "nose enhancement", "nasal surgery"],
    "nose surgery": ["rhinoplasty", "septoplasty", "septorhinoplasty"],
    "rhinoplasty": ["nose job", "nose surgery", "septoplasty", "nose reshaping"],
    "tummy tuck": ["abdominoplasty", "stomach reduction", "abdominal surgery"],
    "abdominoplasty": ["tummy tuck", "stomach reduction", "abdominal surgery"],
    "lip job": ["lip augmentation", "lip fillers", "lip enhancement"],
    "boob job": ["breast augmentation", "breast implants", "breast enhancement", "breast surgery"],
    "breast augmentation": ["breast implants", "boob job", "breast enhancement"],
    "face lift": ["rhytidectomy", "facial rejuvenation", "face surgery"],
    "rhytidectomy": ["face lift", "facial rejuvenation"],
    "brow lift": ["forehead lift", "browplasty", "eyebrow lift"],
    "eyelid surgery": ["blepharoplasty", "eye lift", "eyelid lift"],
    "butt lift": ["brazilian butt lift", "bbl", "gluteoplasty", "buttock augmentation"],
    "brazilian butt lift": ["bbl", "butt lift", "gluteoplasty"],
    "hair restoration": ["hair transplant", "hair implants", "fue", "follicular unit extraction"],
    "liposuction": ["lipo", "fat removal", "body contouring", "liposculpture"],
    
    // Recovery related terms
    "recovery": ["post-surgery", "healing", "recuperation", "aftercare", "post-op"],
    "post-op": ["recovery", "healing", "after surgery", "post-surgical"],
    "healing": ["recovery", "post-op", "recuperation"],
    "pain": ["discomfort", "soreness", "aching", "pain management", "pain relief"],
    "swelling": ["edema", "inflammation", "puffiness", "bloating"],
    "scarring": ["scars", "scar management", "scar treatment", "scar healing"],
    "bruising": ["ecchymosis", "discoloration", "black and blue"],
    
    // Complication related terms
    "complications": ["side effects", "risks", "adverse effects", "problems"],
    "infection": ["bacterial infection", "wound infection", "post-surgical infection"],
    "revision": ["corrective surgery", "secondary surgery", "touch-up"],
    
    // Cost related terms
    "cost": ["price", "fees", "expenses", "financing", "payment"],
    "financing": ["payment plans", "emi", "loans", "cost", "payment options"],
    
    // Results related terms
    "results": ["outcome", "after photos", "before and after", "transformation"],
    "before and after": ["results", "outcome", "transformation", "photos"],
    
    // Procedure related general terms
    "non-surgical": ["non-invasive", "minimally invasive", "no surgery"],
    "surgical": ["invasive", "operation", "surgery"],
    "downtime": ["recovery time", "time off", "healing period"]
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = medicalTermsDictionary;
}