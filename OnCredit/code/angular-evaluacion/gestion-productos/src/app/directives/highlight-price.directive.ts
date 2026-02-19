import { Directive, ElementRef, Input, Renderer2 } from '@angular/core';

@Directive({
  selector: '[appHighlightPrice]'
})
export class HighlightPriceDirective {

  @Input() set appHighlightPrice(price: number | string) {
    let numericPrice: number;
    if (typeof price === 'string') {
      numericPrice = Number(price);
      if (isNaN(numericPrice)) {
        numericPrice = 0; // Or handle the NaN case appropriately
      }
    } else {
      numericPrice = price;
    }
    // ... rest of your directive logic using numericPrice ...
    if (numericPrice > 100) {
      this.renderer.setStyle(this.el.nativeElement, 'color', 'red');
    }
  }

  constructor(private el: ElementRef, private renderer: Renderer2) { }

}