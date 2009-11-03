// common.js should be included before this file.

function createItemHTML(book){
    return dataListEntry(book, book.title, defaultActions('books', book), defaultTags());
}

function editItem(){

}

jQuery(function(){
    jQuery.getJSON('/api/books/list/', {}, function(books){
        var book = {};
        var html = [];
        for (var i = 0, len = books.length; i < len; ++i){
            book = books[i];
            html.push(createItemHTML(book));
        }
        jQuery('#data-list').html(html.join(''));
    });

    function fetch_information(event){
        var elem = jQuery(this),
            value = elem.val(),
            form = elem.parents('form'),
            isbn = ISBN.parse(value);

        if (isbn){
            var isbn10 = isbn.asIsbn10(),
                isbn13 = isbn.asIsbn13();
            jQuery.getJSON('http://openlibrary.org/api/books?bibkeys=ISBN%3A' + isbn13 + '&details=true&' + 'callback=?',
                function(book){
                    if (book){
                        book = book['ISBN:' + isbn13];

                        var authors = [], _authors = book.details.authors;
                        for (var i = 0, len = _authors.length; i < len; i++){
                            authors.push(_authors[i].name);
                        }
                        authors = authors.join(', ');

                        jQuery('input[name="authors"]', form).val(authors);
                        jQuery('input[name="title"]', form).val(book.details.title);
                        jQuery('input[name="isbn_10"]', form).val(isbn10);
                        jQuery('input[name="isbn_13"]', form).val(isbn13);
                        jQuery('input[name="info_url"]', form).val(book.info_url);
                        jQuery('img.cover', form).attr('src', ['http://covers.openlibrary.org/b/isbn/', isbn10, '-M.jpg'].join(''));
                        jQuery('input[type="submit"]', form).removeAttr('disabled');
                    } else {
                        jQuery('input[type="text"]', form).not('input[name="isbn"]').val('');
                        jQuery('input[type="submit"]', form).attr('disabled', 'disabled');
                    }
                }
            );
        } else {
            jQuery('input[type="text"]', form).not('input[name="isbn"]').val('');
            jQuery('input[type="submit"]', form).attr('disabled', 'disabled');
        }
    };

    jQuery('form.edit input[name="isbn"], form.new input[name="isbn"]')
        .live('change', fetch_information)
        .live('keyup', fetch_information);
});

