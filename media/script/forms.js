String.prototype.startsWith = function(str)
{return (this.match("^"+str)==str)}

/*
String.prototype.endsWith = function(str)
{return (this.match(str+"$")==str)}
*/

String.prototype.isUpperCase = function(){
   return !!this.match(/^[^a-z]*$/);
}
String.prototype.isLowerCase = function(){
   return !!this.match(/^[^A-Z]*$/);
}
String.prototype.isSameCase = function(){
   return (this.isLowerCase() || this.isUpperCase());
}
String.prototype.sanitizeCapitalization = function(){
   // Requires the titlecaps function by john resig.
   if(this && this.isSameCase()){
       return titleCaps(this.toLowerCase());
   } else {
       return this;
   }
}

jQuery(function(){
    var elements = {
        mobile_or_phone_fields: jQuery('form input.mobile, form input.phone'),
        form_decorated_fields: jQuery('form.decorated-fields'),
        url_fields: jQuery('form input.url'),
        capitalization_fields: jQuery('form input.capitalize')
    }, HTTP = "http://";

    elements.mobile_or_phone_fields.numeric({allow: '+-() '});
    elements.url_fields.keyup(function(event){
        var elem = jQuery(this), value = elem.val();
        if (value == 'http:/'){
            // For now handle only one common case where the user may press a backspace
            // to clear the last front slash.
            elem.val(HTTP);
        } else if (!value.startsWith(HTTP)){
            elem.val(HTTP + value);
        }
    });
    elements.capitalization_fields.live('change', function(event){
       var o = jQuery(this), value = jQuery.trim(o.val());
       o.val(value.sanitizeCapitalization());
    });

    elements.form_decorated_fields.validate({
        rules: {
            presentation: {
              //required: true,
              accept: "ppt|doc|pdf"
            },
            mobile_number: {
                mobile: true
            },
            phone_number: {
                phone: true
            }
        },
        messages: {
            presentation: {
                accept: "Please upload a PowerPoint presentation, a Word document, or a PDF document only."
            }
        }
    });
});

