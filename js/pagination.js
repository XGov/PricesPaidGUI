// destroy pagination  if it exists and recreate...
// This is needed to keep jqPaginate from getting confused, 
// I don't know why.  I should send them email about it.
function recreatePagination() {
    var html = "";
    html += '<div class="large pagination">';
    html += '<a href="#" class="first" data-action="first">&laquo;</a>';
    html += '<a href="#" class="previous" data-action="previous">&lsaquo;</a>';
    html += '<input type="text" readonly="readonly" data-max-page="40" />';
    html += '<a href="#" class="next" data-action="next">&rsaquo;</a>';
    html += '<a href="#" class="last" data-action="last">&raquo;</a>';
    html += '</div>';
    $('#paginationHolder1').html(html);

// I can't use the second paginator until I tie everything together with
// javascript --- this will take too much time.
//    var wrappedHtml = '<p>'+html+'</p>';
//    $('#paginationHolder2').html(wrappedHtml);
}
