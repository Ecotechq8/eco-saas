# -*- coding: utf-8 -*-

import textwrap


class Number2Words:
    """Convert numbers to words"""
    
    def __init__(self):
        self.units = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        self.teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        self.tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert(self, number):
        """Convert a number to words"""
        if number == 0:
            return 'Zero'
        
        result = []
        
        if number >= 10000000:
            result.append(self.units[number // 10000000] + ' Crore')
            number %= 10000000
        
        if number >= 100000:
            result.append(self._convert_hundreds(number // 100000) + ' Lakh')
            number %= 100000
        
        if number >= 1000:
            result.append(self._convert_hundreds(number // 1000) + ' Thousand')
            number %= 1000
        
        if number > 0:
            result.append(self._convert_hundreds(number))
        
        return ' '.join(result)
    
    def _convert_hundreds(self, num):
        """Convert a number less than 1000 to words"""
        if num == 0:
            return ''
        
        result = []
        
        if num >= 100:
            result.append(self.units[num // 100] + ' Hundred')
            num %= 100
        
        if num >= 20:
            result.append(self.tens[num // 10])
            num %= 10
        
        if num >= 10:
            result.append(self.teens[num - 10])
            num = 0
        
        if num > 0:
            result.append(self.units[num])
        
        return ' '.join(result)
