///////////////////////////BANNER RIGHT///////////////////////////////////
document.addEventListener('DOMContentLoaded', function() {
    const bannerContainer = document.getElementById('banner-container');
    const skeletonTemplate = document.getElementById('skeleton-banner-template');

    // Append skeleton banners to the container
    for (let i = 0; i < 3; i++) {
        bannerContainer.append(skeletonTemplate.content.cloneNode(true));
    }

    // Fetch actual banner data
    fetch("/api/banners/")
        .then(res => res.json())
        .then(banners => {
            // Clear the skeletons
            bannerContainer.innerHTML = '';

            // Populate the container with actual banner data
            banners.forEach(banner => {
                const bannerHTML = `
                    <div class="banner banner-overlay banner-sm content-right shadow-sm">
                        <a href="${banner.link}">
                            <img src="${banner.image}" alt="Banner">
                        </a>
                        <div class="banner-content text-right">
                            <h4 class="banner-subtitle">${banner.title}</h4>
                            <h4 class="banner-price">Save<span class="price">$19,99</span></h4>
                            <a href="#" class="banner-link">Buy Now<i class="icon-long-arrow-right"></i></a>
                        </div>
                    </div><!-- End .banner -->
                `;
                bannerContainer.insertAdjacentHTML('beforeend', bannerHTML);
            });
        })
        .catch(error => {
            console.error('Error fetching banner data:', error);
        });
});
//////////////////////////BANNER END/////////////////////////////


////////////////////////////BANNER LEFT///////////////////////////
document.addEventListener('DOMContentLoaded', function() {
    const bannerContainer = document.getElementById('banner-container-1');
    const skeletonTemplate = document.getElementById('skeleton-banner-1-template');

    // Append skeleton banners to the container
    for (let i = 0; i < 3; i++) {
        bannerContainer.append(skeletonTemplate.content.cloneNode(true));
    }

    // Fetch actual banner data
    fetch("/api/banners/1/")
        .then(res => res.json())
        .then(banners => {
            // Clear the skeletons
            bannerContainer.innerHTML = '';

            // Populate the container with actual banner data
            banners.forEach(banner => {
                const bannerHTML = `
                    <div class="banner banner-overlay banner-sm content-right shadow-sm">
                        <a href="${banner.link}">
                            <img src="${banner.image}" alt="Banner">
                        </a>
                        <div class="banner-content text-right">
                            <h4 class="banner-subtitle">${banner.title}</h4>
                            <h4 class="banner-price">Save<span class="price">$19,99</span></h4>
                            <a href="#" class="banner-link">Buy Now<i class="icon-long-arrow-right"></i></a>
                        </div>
                    </div><!-- End .banner -->
                `;
                bannerContainer.insertAdjacentHTML('beforeend', bannerHTML);
            });
        })
        .catch(error => {
            console.error('Error fetching banner data:', error);
        });
});
///////////////////////////////////////////////////////


///////////////////////BOOK////////////////////////////////

document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.getElementById('book-carousel');
    const skeletonTemplate = document.getElementById('skeleton-card-template');

    // Append skeleton cards to the carousel
    for (let i = 0; i < 10; i++) {
        carousel.append(skeletonTemplate.content.cloneNode(true));
    }

    // Fetch actual product data
    fetch("/loading/")  // Change this URL to the actual endpoint that returns book data
        .then(res => res.json())
        .then(products => {
            // Clear the skeletons
            carousel.innerHTML = '';

            // Populate the carousel with actual product data
            products.forEach(product => {
                const productHTML = `
                    <div class="product">
                        <figure class="product-media">
                            <a href="${product.url}">
                                <img src="${product.image}" alt="${product.title}" class="product-image">
                            </a>
                        </figure><!-- End .product-media -->

                        <div class="product-body">
                            <div class="product-cat">
                                ${product.type === 'Book' ? `by <a href="#">${product.brand}</a>` : `<a href="${product.sub_category_url}">${product.sub_category}</a>`}
                            </div><!-- End .product-cat -->
                            <h3 class="product-title"><a href="${product.url}">${product.title}</a></h3><!-- End .product-title -->
                            <div class="product-price">
                                <span class="new-price">${product.price}</span>
                            </div><!-- End .product-price -->
                        </div><!-- End .product-body -->
                    </div><!-- End .product -->
                `;
                carousel.insertAdjacentHTML('beforeend', productHTML);
            });

            // Reinitialize the carousel after adding new items
            $(carousel).trigger('destroy.owl.carousel');
            $(carousel).owlCarousel($(carousel).data('owl-options'));
        })
        .catch(error => {
            console.error('Error fetching product data:', error);
        });
});
///////////////////////////////////////////////////////

///////////////////////////////////////////////////////
document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.getElementById('slider-carousel');
    const skeletonTemplate = document.getElementById('skeleton-slide-template');

    // Append skeleton slides to the carousel
    for (let i = 0; i < 1; i++) { // Only 1 skeleton for large carousel
        carousel.append(skeletonTemplate.content.cloneNode(true));
    }

    // Fetch actual slider data
    fetch("/load-sliders/")  // Change this URL to the actual endpoint that returns slider data
        .then(res => res.json())
        .then(sliders => {
            // Clear the skeletons
            carousel.innerHTML = '';

            // Populate the carousel with actual slider data
            sliders.forEach(slider => {
                const slideHTML = `
                    <div class="intro-slide" style="background-image: url(${slider.image}); background-size: cover; background-position: center;">
                        <div class="container intro-content">
                            <div class="row">
                                <div class="col-auto offset-lg-3 intro-col">
                                    <h3 class="intro-subtitle">${slider.discount_deal}</h3>
                                    <h1 class="intro-title">${slider.brand_name}
                                        <span>
                                            <sup class="font-weight-light">from</sup>
                                            <span class="text-primary">${slider.sale}</span>
                                        </span>
                                    </h1>
                                    <a href="${slider.link}" class="btn btn-outline-primary-2">
                                        <span>Shop Now</span>
                                        <i class="icon-long-arrow-right"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                carousel.insertAdjacentHTML('beforeend', slideHTML);
            });

            // Reinitialize the carousel after adding new items
            $(carousel).trigger('destroy.owl.carousel');
            $(carousel).owlCarousel({
                items: 1,
                nav: true,
                dots: true,
                loop: true
            });
        })
        .catch(error => {
            console.error('Error fetching slider data:', error);
        });
});
///////////////////////////////////////////////////////