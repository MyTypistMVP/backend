Marketplace features inventory — items to port into TemplateService

- Homepage: featured, trending, new templates, promotions
- Search: advanced filters (price, rating, category), sorting, pagination
- Template details: extended metadata, seller info, token_cost, price, special offers
- Purchase flow: purchase_template -> needs to support token-charging/pay-as-you-go and wallet/stripe
- Reviews: add_template_review, update rating aggregates
- Favorites: toggle favourite and user favorites listing
- User purchases: get_user_purchases (records purchases, receipts)
- Marketplace stats: sales, revenue, popular templates

Porting approach:
1. Add wrapper methods to `TemplateService` for: get_marketplace_home, search_marketplace, get_template_details, purchase_template, add_template_review, toggle_favorite, get_user_purchases, get_marketplace_stats.
2. Ensure purchase_template supports token-based charging (deduct tokens for pay-as-you-go users) and credits/credits-decrement for subscription users.
3. Keep original `marketplace.py` backed up and implement a compatibility shim that routes to `TemplateService` wrappers or returns 410 after porting.

Notes:
- Payment and token logic likely interacts with wallet/payment services; confirm and add adapters where necessary.
- Do not delete marketplace assets yet; port functionality first and run tests.
