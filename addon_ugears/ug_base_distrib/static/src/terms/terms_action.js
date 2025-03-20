/** @odoo-module */

import {registry} from "@web/core/registry"

async function termsAction(env, action) {
    let user_rec = await env.services.orm.searchRead('res.users', [['id', '=', env.services.user.userId]], ['distrib_id']),
        distrib_rec
    if (user_rec) {
        let distrib_id = user_rec[0]
        if (distrib_id) {
            let d_id = distrib_id.distrib_id[0]
            distrib_rec = await env.services.orm.searchRead('distrib.distributors', [['id', '=', d_id]], ['currency_id'])
        }
    }
    if (Array.isArray(distrib_rec) && distrib_rec.length > 0) {
        let currency = distrib_rec[0].currency_id
        let cur_str = currency[1].toLowerCase()
        let url = `/ug_base_distrib/static/terms/${cur_str}/Ugears_TnC_2025_${cur_str}.pdf`
        let url_action = {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }
        env.services.action.doAction(url_action)
        return
    }
    let notification = {
        type: 'info',
        sticky: true,
    }
    env.services.notification.add('Nothing to show', notification)
}
registry.category("actions").add("term_action", termsAction)