import { useEffect } from "@odoo/owl";
import { url } from "@web/core/utils/urls";
import { useBus, useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";


export class AppsMenu extends Dropdown {
    setup() {
    	super.setup();
    	this.commandPaletteOpen = false;
        this.commandService = useService("command");
    	this.companyService = useService('company');
    	if (this.companyService.currentCompany.has_background_image) {
            this.imageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image',
                id: this.companyService.currentCompany.id,
            });
    	} else {
    		this.imageUrl = '/eco_theme/static/src/img/background.png';
    	}
        useEffect(
            (isOpen) => {
            	if (isOpen) {
            		const openMainPalette = (ev) => {
            	    	if (
            	    		!this.commandServiceOpen && 
            	    		ev.key.length === 1 &&
            	    		!ev.ctrlKey &&
            	    		!ev.altKey
            	    	) {
	            	        this.commandService.openMainPalette(
            	        		{ searchValue: `/${ev.key}` }, 
            	        		() => { this.commandPaletteOpen = false; }
            	        	);
	            	    	this.commandPaletteOpen = true;
            	    	}
            		}
	            	window.addEventListener("keydown", openMainPalette);
	                return () => {
	                	window.removeEventListener("keydown", openMainPalette);
	                	this.commandPaletteOpen = false;
	                }
            	}
            },
            () => [this.state.isOpen]
		);
    	useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", this.state.close);
    }
    onOpened() {
		super.onOpened();
		if (this.menuRef && this.menuRef.el) {
			this.menuRef.el.style.backgroundImage = `url('${this.imageUrl}')`;
		}
    }
}


const unwantedKeys = [
    "odoo_account",
    "documentation",
    "shortcuts",
    "developer",
    "odoo_account_tutorial",
    "odoo_account_upgrade",
    "tour_enabled"
];

unwantedKeys.forEach(key => {
    registry.category("user_menuitems").remove(key);
    console.log(key);
});



