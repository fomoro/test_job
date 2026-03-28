public class Payment {
    // 3. Encapsulation
    private decimal _amount;
    public decimal Amount => _amount;

    // 5. Constructor
    public Payment(decimal amount) => _amount = amount;

    // 2. Polymorphism (Virtual)
    public virtual void Process() => Console.WriteLine($"Processing {Amount}");

    // 4. Overloading
    public void Process(int installments) => Console.WriteLine($"Processing {Amount} in {installments} installments");
}

// 1. Inheritance
public class CreditCardPayment : Payment {
    public CreditCardPayment(decimal amount) : base(amount) { }

    // 2. Polymorphism (Override)
    public override void Process() => Console.WriteLine($"Authorizing Card: {Amount}");
}